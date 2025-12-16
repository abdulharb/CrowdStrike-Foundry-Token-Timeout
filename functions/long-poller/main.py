import time
import logging
import jwt
from typing import Dict, Any, Union
from logging import Logger
from falconpy import Hosts
from crowdstrike.foundry.function import Function, Request, Response, APIError


func = Function.instance()

MAX_DURATION = 660 
POLL_INTERVAL = 60

@func.handler(method='POST', path='/poll')
def on_post(request: Request, config: Union[Dict[str, Any], None], logger: Logger) -> Response:
    """
    Polls the CrowdStrike Hosts API for a specified duration to test function lifespan.
    Also decodes the access token to log its expiration.
    """
    start_time = time.time()
    logger.info(f"Starting long polling function at {start_time:.2f}. Target duration: {MAX_DURATION}s")

    # Decode and log token info
    try:
        if hasattr(request, 'access_token'):
            # Decode without verification as we just want to inspect claims
            token_data = jwt.decode(request.access_token, options={"verify_signature": False})
            exp_time = token_data.get('exp')
            if exp_time:
                time_until_exp = exp_time - start_time
                logger.info(f"Token Expiration Time: {exp_time}")
                logger.info(f"Token Time to Live: {time_until_exp:.2f} seconds")
                if time_until_exp < MAX_DURATION:
                    logger.warning(f"WARNING: Token is set to expire in {time_until_exp:.2f}s, which is less than the target duration of {MAX_DURATION}s!")
            else:
                logger.warning("Token has no 'exp' claim.")
        else:
            logger.warning("Request object has no 'access_token' attribute.")
    except Exception as e:
        logger.error(f"Failed to decode token: {str(e)}")


    # Initialize FalconPy Hosts client
    # It automatically uses the Foundry execution context for authentication
    falcon = Hosts()

    iteration = 0
    
    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            if elapsed >= MAX_DURATION:
                logger.info(f"Reached maximum duration of {MAX_DURATION}s. Stopping.")
                break

            iteration += 1
            logger.info(f"Iteration {iteration}: Elapsed {elapsed:.2f}s. Polling API...")

            # Simple API call to keep the connection/token active and prove we can still talk to the API
            # We request 1 device just to ping the service
            response = falcon.query_devices_by_filter(limit=1)
            
            if response["status_code"] == 200:
                logger.info(f"API Call Success. Request ID: {response['headers'].get('X-Cs-Traceid', 'N/A')}")
            else:
                logger.error(f"API Call Failed: {response['status_code']} - {response['body']}")
                # We don't break on error, we try to keep going to test lifespan, unless it's a completely fatal token error.
                # But usually 401 would indicate token expiry.
                if response["status_code"] == 401:
                    logger.error("Token expired?!")
                    return Response(
                        body={
                            'message': 'Token expired',
                            'duration_seconds': elapsed,
                            'iterations': iteration
                        },
                        code=200,
                    )

            # Wait for next poll
            # Adjust sleep to not overshoot MAX_DURATION
            time_remaining = MAX_DURATION - (time.time() - start_time)
            if time_remaining <= 0:
                break
            
            sleep_time = min(POLL_INTERVAL, time_remaining)
            time.sleep(sleep_time)

        total_time = time.time() - start_time
        logger.info(f"Function completed successfully after {total_time:.2f}s")
        
        return Response(
            body={
                'message': 'Long polling completed successfully',
                'duration_seconds': total_time,
                'iterations': iteration
            },
            code=200,
        )

    except Exception as e:
        logger.error(f"Function crashed: {str(e)}")
        return Response(
            body={
                'message': f'Function crashed: {str(e)}',
                'duration_seconds': time.time() - start_time,
                'iterations': iteration
            },
            code=200,
        )

if __name__ == '__main__':
    func.run()
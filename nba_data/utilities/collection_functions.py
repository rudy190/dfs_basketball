from datetime import datetime
import requests

def request_data(url, params, headers, Proxies):
    proxy = Proxies.get_proxy()
    try:
        req_response = requests.get(url,
                                    params=params,
                                    headers=headers,
                                    proxies=proxy['proxy_address'])
        Proxies.put_proxy(proxy['proxy_address'])
    except:
        print('Request timeout error with base_url: {}'.format(url))
        print('Request timeout error with params: {}'.format(params))
        Proxies.timeout_proxy(proxy['proxy_address'], datetime.now())
        req_response = request_data(url, params, headers)
    return req_response

def set_status_values(req_response):
    status_code = req_response.status_code
    status_reason = req_response.reason
    return status_code, status_reason

def update_status_reason(reason):
    status_reason = reason
    return status_reason

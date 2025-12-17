"""
OCR.space API helper functions.
Matches the exact format from OCR.space documentation.
"""
import os
import requests
import logging

logger = logging.getLogger('credentials')


def ocr_space_file(filename, overlay=False, api_key='helloworld', language='eng'):
    """
    OCR.space API request with local file.
    Python3.5+ - matches OCR.space documentation exactly.
    
    :param filename: Your file path & name.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld' (free demo key).
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'eng'.
    :return: Result in JSON format (decoded string).
    """
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
    }
    
    with open(filename, 'rb') as f:
        r = requests.post(
            'https://api.ocr.space/parse/image',
            files={os.path.basename(filename): f},  # Use basename as key
            data=payload,
            timeout=30
        )
    return r.content.decode()


def ocr_space_url(url, overlay=False, api_key='helloworld', language='eng'):
    """
    OCR.space API request with remote file.
    Python3.5+ - matches OCR.space documentation exactly.
    
    :param url: Image url.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld' (free demo key).
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'eng'.
    :return: Result in JSON format (decoded string).
    """
    payload = {
        'url': url,
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
    }
    
    r = requests.post(
        'https://api.ocr.space/parse/image',
        data=payload,
        timeout=30
    )
    return r.content.decode()





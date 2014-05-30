#!/usr/bin/env python
# vim: set ts=2 expandtab:
'''
Module: bing.py
Desc: Translate strings via Bing traslate
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, May 29th 2014

Simple use of Bing translate API in blocking manner.
after http://stackoverflow.com/questions/12017846/microsoft-translator-api-in-python
  
'''
import argparse
import json
import requests
import urllib

def translate(text, from_language=u'ja', to_language=u'en', secret_key=u''):
  if not secret_key:
    raise Exception(u'No Microsoft Azure secret key provided on bing.translate call.')

  args = {
          'client_id': 'arib_CCs_auto_translate',
          'client_secret': secret_key.decode('utf-8'),#your azure secret here
          'scope': 'http://api.microsofttranslator.com',
          'grant_type': 'client_credentials'
      }
  oauth_url = u'https://datamarket.accesscontrol.windows.net/v2/OAuth2-13'
  oauth_junk = json.loads(requests.post(oauth_url,data=urllib.urlencode(args)).content)
  translation_args = {
          'text': text.encode('utf-8'),
          'to': to_language.encode('utf-8'),
          'from': from_language.encode('utf-8'),
          }
  headers={'Authorization': 'Bearer '+oauth_junk['access_token']}
  translation_url = 'http://api.microsofttranslator.com/V2/Ajax.svc/Translate?'
  translation_result = requests.get(translation_url+urllib.urlencode(translation_args),headers=headers)
  return translation_result.content.decode('utf-8')

def main():

  parser = argparse.ArgumentParser(description='Exercise bing translation api.')
  parser.add_argument('text', help='Input filename (MPEG2 Elmentary Stream)', type=str)
  parser.add_argument('-k', '--secret_key', help='Windows secret key for bing translate API.', type=str, default='')
  args = parser.parse_args()

  text = args.text
  secret_key = args.secret_key
  translation = translate(text, secret_key=secret_key)
  print(translation)

if __name__ == "__main__":
  main()

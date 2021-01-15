# -*- coding: utf-8 -*-
"""
Created on Fri Jan  1 18:37:06 2021

@author: oc3512
"""
import pyperclip
import re

phone_regex = re.compile(r'''(
    (0\d{1,4}|\(0\d{1,4}\))?
    (\s|-)?
    (\d{1,4})
    (\s|-)
    (\d{4})
    (\s*(Extension|\(Extension\)|\(Ext.{1,3}\))\s*(\d{2,5}))?
    )''',re.VERBOSE)

mail_regex = re.compile(r'''(
    [a-zA-Z0-9._%+-]+
    @
    [a-zA-Z0-9.-]+
    (\.[a-zA-Z]{2,4})
    )''',re.VERBOSE)

text = str(pyperclip.paste())
matches = []

for groups in phone_regex.findall(text):
    phone_num = '-'.join([groups[1], groups[3], groups[5]])
    if groups[8] != '':
        phone_num += ' Extension'+ groups[8]
    matches.append(phone_num)

for groups in mail_regex.findall(text):
    matches.append(groups[0])

if len(matches) > 0:
    pyperclip.copy('\n'.join(matches))
    print('Copied in the clipboard')
    print('\n'.join(matches))
else:
    print('No telephone numbers or email address were found')

input('Please enter any key to end')
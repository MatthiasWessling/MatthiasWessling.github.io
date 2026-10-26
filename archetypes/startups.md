+++
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
date = '{{ .Date }}'
draft = true
summary = ''
founded_year = '{{ dateFormat "2006" .Date }}'
organization = ''
role = 'Startup support'
status = 'Active'
location = ''
website = ''
topics = []
image = ''
image_alt = ''
featured = false
+++

## Focus

{{ .Params.summary }}

## Context

Brief notes on technology, team, and relationship to the research groups.

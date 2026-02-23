+++
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
date = '{{ .Date }}'
draft = true
summary = ''
tech_stack = []
project_url = ''
github_url = ''
image = ''
image_alt = ''
featured = false
+++

## Overview

{{ .Params.summary }}

## Technology Stack

{{ range .Params.tech_stack }}
- {{ . }}
{{ end }}

## Details

Your project details go here...
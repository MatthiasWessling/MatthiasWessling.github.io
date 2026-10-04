+++
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
date = '{{ .Date }}'
draft = true
summary = ''
abstract = ''
authors = ['Matthias Wessling']
publication = ''
publication_year = '{{ dateFormat "2006" .Date }}'
doi = ''
paper_url = ''
openalex_id = ''
cited_by_count = 0
source = 'manual'
tags = []
+++

## Abstract

{{ .Params.abstract }}

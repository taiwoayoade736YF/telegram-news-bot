# get the response headers and if it's too big of a file (2MB for now), log it and skip
r_headers = dict(response.info())
if 'content-length' in r_headers:
	if int(r_headers['content-length']) > 2097152:
		print('URL Rejected: file length > 2mb')
		log_rejected_url(url, 'file length > 2mb')
    continue
html = response.read()
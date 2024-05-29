import requests

params = {'access_token': '<your-access-token>'}

# Create the deposit resource
url = "https://sandbox.zenodo.org/api/deposit/depositions"
headers = {"Content-Type": "application/json"}

res = requests.post(
    url,
    json={},
    # Headers are not necessary here since "requests" automatically
    # adds "Content-Type: application/json", because we're using
    # the "json=" keyword argument...
    # headers=headers,
    params=params,
)
print(res.json())

# In the new files API we use a PUT request to a 'bucket' link, which is the container for files
# bucket url looks like this: 'https://sandbox.zenodo.org/api/files/12341234-abcd-1234-abcd-0e62efee00c0'
bucket_url = res.json()['links']['bucket']

# We pass the file object (fp) directly to request as 'data' for stream upload
# the target URL is the URL of the bucket and the desired filename on Zenodo seprated by slash
with open('/path/to/my-file.zip', 'rb') as fp:
    res = requests.put(
        bucket_url + '/my-file.zip',
        data=fp,
        # No headers included in the request, since it's a raw byte request
        params=params,
    )
print(res.json())
# Recuitee Report aggregator

Recruitee API:
    
    https://api.recruitee.com/docs/index.html
    
Provide the `.env` file with following fields:
    
    AUTH_TOKEN=<auth_key>
    
    <company_name_0>=<company_id>
    <company_name_1>=<company_id>
    ...
    ..
    . 

so you can call api client with

    client = get_client('company_name_0')

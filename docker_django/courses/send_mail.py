
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from django.conf import settings

def subscribe_user_to_mailchimp(email, first_name=None, last_name=None):
    client = MailchimpMarketing.Client()
    client.set_config({
        "api_key": settings.MAILCHIMP_API_KEY,
        "server": settings.MAILCHIMP_SERVER_PREFIX
    })

    list_id = settings.MAILCHIMP_LIST_ID
    member_info = {
        "email_address": email,
        "status": "subscribed",  # Hoặc "pending" nếu bạn muốn xác thực email
        "merge_fields": {
            "FNAME": first_name or "",
            "LNAME": last_name or ""
        }
    }

    try:
        response = client.lists.add_list_member(list_id, member_info)
        print("Mailchimp response:", response)
        return response
    except ApiClientError as error:
        print(f"Mailchimp error: {error.text}")
        return None

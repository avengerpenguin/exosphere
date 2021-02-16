from exosphere.stacks import static_site, static_site_with_email


def staticsite(domain, region="eu-west-2", subdomain=None):
    static_site.update(domain, region=region, subdomain=subdomain)


def staticsitewithemail(
    domain, from_address, forwarding_addresses, region="eu-west-2"
):
    static_site_with_email.update(
        domain, from_address, forwarding_addresses, region=region
    )

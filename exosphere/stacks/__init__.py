from exosphere.stacks import static_site_with_email, static_site


def staticsite(domain, region='eu-west-2'):
    static_site.update(domain, region='eu-west-2')


def staticsitewithemail(domain, from_address, forwarding_addresses, region='eu-west-2'):
    static_site_with_email.update(domain, from_address, forwarding_addresses, region='eu-west-2')

from ipaddress import IPv4Address, IPv4Network


def check_ip_in_subnets(request, subnets: list):
    ip_addr = __get_source_ip(request)
    ip = IPv4Address(ip_addr)
    hit = False
    for subnet in subnets:
        hit = ip in IPv4Network(subnet)
        if hit:
            break
    return hit


def __get_source_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

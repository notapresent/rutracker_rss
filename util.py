import datetime
import email


def datetime_to_timestamp(dt):
    """Convert naive datetime to POSIX timestamp"""
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds()


def datetime_to_rfc822(dt):
    """Formats datetime object as RFC822 time string"""
    ts = datetime_to_timestamp(dt)
    return email.utils.formatdate(ts)

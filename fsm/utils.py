import re
from pathlib import Path

SSH_CONFIG_FILE = "~/.ssh/config"
SSH_KNOWN_HOSTS = "~/.ssh/known_hosts"
REP_DICT = {",": "-", ".": "-", " ": "-"}


def clean_session_name(session_name):
    """
    Create session name that respect the guidelines of `libtmux`.
    """
    for start, end in REP_DICT.items():
        session_name = session_name.replace(start, end)

    return session_name


def get_known_hosts() -> list[set]:
    """
    Get known hosts from `~/.ssh/known_hosts` file.

    Return a list of sets with all the hostnames,
    pruned by removing duplicate keys.
    """

    ssh_known_hosts_path = Path(SSH_KNOWN_HOSTS).expanduser()
    if not ssh_known_hosts_path.exists():
        return list()

    ssh_known_hosts: list[set] = []
    with open(ssh_known_hosts_path, "r") as f:
        for line in f.readlines():
            hosts = line.split(" ")[0]
            found_hosts = set(hosts.split(","))

            some_found = False
            for i, known in enumerate(ssh_known_hosts):
                if found_hosts.intersection(known):
                    ssh_known_hosts[i] = known.union(found_hosts)
                    some_found = True

            if not some_found:
                ssh_known_hosts.append(found_hosts)

    return ssh_known_hosts


def get_hosts(reversed=False) -> dict:
    """
    Get hosts from ~/.ssh/config file.

    Return a dict with the pairs (host, hostname/ip),
    only for the entries in `config` for which the ip or hostname
    are specified.
    """
    ssh_config_path = Path(SSH_CONFIG_FILE).expanduser()
    if not ssh_config_path.exists():
        return dict()

    ssh_hosts = dict()
    with open(ssh_config_path, "r") as f:
        content = f.read().split("\n\n")
        for block in content:
            parsed_block = {}
            for line in block.split("\n"):
                line = line.strip()
                # pattern definition
                host_pattern = re.compile(r"Host ([a-zA-Z]+)")
                hostname_pattern = re.compile(r"HostName (.*)")

                # pattern match
                host_match = host_pattern.match(line)
                hostname_match = hostname_pattern.match(line)

                if host_match:
                    parsed_block["host"] = host_match.group(1)
                if hostname_match:
                    parsed_block["hostname"] = hostname_match.group(1)

            if "host" in parsed_block and "hostname" in parsed_block:
                if reversed:
                    ssh_hosts[parsed_block["host"]] = parsed_block["hostname"]
                else:
                    ssh_hosts[parsed_block["hostname"]] = parsed_block["host"]

    return ssh_hosts

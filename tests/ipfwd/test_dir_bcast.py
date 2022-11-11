import pytest

from tests.common.fixtures.ptfhost_utils import copy_ptftests_directory   # lgtm[py/unused-import]
from tests.ptf_runner import ptf_runner
from datetime import datetime

pytestmark = [
    pytest.mark.topology('t0', 'm0', 'mx')
]

def test_dir_bcast(duthosts, rand_one_dut_hostname, ptfhost, tbinfo):
    duthost = duthosts[rand_one_dut_hostname]
    testbed_type = tbinfo['topo']['name']

    # Copy VLAN information file to PTF-docker
    mg_facts = duthost.get_extended_minigraph_facts(tbinfo)

    # Filter expected_vlans and minigraph_vlans to support t0-56-po2vlan topology
    expected_vlans = []
    minigraph_vlans = {}
    for vlan in mg_facts['minigraph_vlan_interfaces']:
        vlan_name = vlan['attachto']
        if len(mg_facts['minigraph_vlans'][vlan_name]['members']) > 1:
            expected_vlans.append(vlan)
            vlan_members = []
            for vl_m in mg_facts['minigraph_vlans'][vlan_name]['members']:
                if 'PortChannel' not in vl_m:
                    vlan_members.append(vl_m)
            minigraph_vlans[vlan_name] = {'name': vlan_name, 'members': vlan_members}

    extra_vars = {
        'minigraph_vlan_interfaces': expected_vlans,
        'minigraph_vlans':           minigraph_vlans,
        'minigraph_port_indices':    mg_facts['minigraph_ptf_indices'],
        'minigraph_portchannels':    mg_facts['minigraph_portchannels']
    }
    ptfhost.host.options['variable_manager'].extra_vars.update(extra_vars)
    ptfhost.template(src="../ansible/roles/test/templates/fdb.j2", dest="/root/vlan_info.txt")

    # Start PTF runner
    params = {
        'testbed_type': testbed_type,
        'router_mac': duthost.facts['router_mac'],
        'vlan_info': '/root/vlan_info.txt'
    }
    log_file = "/tmp/dir_bcast.BcastTest.{}.log".format(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
    ptf_runner(
        ptfhost,
        'ptftests',
        'dir_bcast_test.BcastTest',
        '/root/ptftests',
        params=params,
        log_file=log_file,
        is_python3=True)

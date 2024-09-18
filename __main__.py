"""An OpenStack Python Pulumi program"""

import pulumi
from pulumi_openstack import images
from pulumi_openstack import compute
from pulumi_openstack import networking
from pulumi_openstack import blockstorage

lan_net = networking.Network("nodes-net", admin_state_up=True)
subnet = networking.Subnet(
    "nodes-subnet",
    network_id=lan_net.id,
    cidr="192.168.99.0/24",
    ip_version=4,
    dns_nameservers=["1.1.1.1", "9.9.9.9"],
)

# Create a router (to connect the subnet to internet)
router = networking.Router(
    "nodes-router",
    admin_state_up=True,
    external_network_id="0f9c3806-bd21-490f-918d-4a6d1c648489",
)
router_interface1 = networking.RouterInterface(
    "routerInterface", router_id=router.id, subnet_id=subnet.id
)

node_secgroup = networking.SecGroup(
    "node_secgroup", description="My neutron security group"
)
networking.SecGroupRule(
    "ingress-allow-everything",
    direction="ingress",
    ethertype="IPv4",
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=node_secgroup.id,
)


talos_image = images.Image("talos-image",
    local_file_path="talos-omni-v1.7.4.iso",
    container_format="bare",
    decompress=True,
    disk_format="iso",
    name="talos-omni",
    visibility="private")

for node in ["node-1", "node-2", "node-3"]:

  instance_worker = compute.Instance(
      node,
      flavor_name="a1-ram2-disk20-perf1",
      image_name=talos_image.name,
      networks=[{"name": lan_net.name}],
      security_groups=[node_secgroup.name],
  )

  volume = blockstorage.Volume(node, size=50, name=node)
  compute.VolumeAttach(node,
    instance_id=instance_worker.id,
    volume_id=volume.id) 
  
  floating_ip_admin = compute.FloatingIp(node, pool="ext-floating1")
  floating_ip_admin_associate = compute.FloatingIpAssociate(
      f"floating-ip-{node}",
      floating_ip=floating_ip_admin.address,
      instance_id=instance_worker.id,
      fixed_ip=instance_worker.networks[0].fixed_ip_v4,
  )


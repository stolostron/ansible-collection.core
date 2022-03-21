#!/usr/bin/env bash

if [ ! -d "inventory" ]; then
mkdir inventory
fi
# check if inventory can work
ansible-playbook create_inventory.yml -e @../../integration_config.yml "$@"

echo 'created inventory file'
cat inventory/inventory_ocm.yml
ansible-inventory -i inventory/inventory_ocm.yml --list
# verify inventory results
ansible-playbook -i inventory/inventory_ocm.yml test_inventory.yml  -e @../../integration_config.yml "$@"

from oslo_config import cfg


class LimitsV2(object):
    def on_get(self, req, resp, tenant_id):
        client = req.sl_client

        account = client['Account'].getObject(
            mask='mask[hourlyVirtualGuestCount]')

        limits = {
            'absolute': {
                'maxImageMeta': cfg.CONF.compute.default_metadata_items,
                'maxPersonality': cfg.CONF.compute.default_injected_files,
                'maxPersonalitySize':
                cfg.CONF.compute.default_injected_file_content_bytes,
                'maxSecurityGroupRules':
                cfg.CONF.compute.default_security_group_rules,
                'maxSecurityGroups': cfg.CONF.compute.default_security_groups,
                'maxServerMeta': cfg.CONF.compute.default_metadata_items,
                'maxTotalCores': cfg.CONF.compute.default_cores,
                'maxTotalFloatingIps': cfg.CONF.compute.default_floating_ips,
                'maxTotalInstances': cfg.CONF.compute.default_instances,
                'maxTotalKeypairs': cfg.CONF.compute.default_key_pairs,
                'maxTotalRAMSize': cfg.CONF.compute.default_ram,
                'totalInstancesUsed': account['hourlyVirtualGuestCount'],
                'totalCoresUsed': 0,
                'totalRAMUsed': 0,
                'totalFloatingIpsUsed': 0,
                'totalSecurityGroupsUsed': 0,
            },
            # TODO(imkarrer) - Added rate to make tempest pass, need real rate
            'rate': [],
        }

        resp.body = {'limits': limits}

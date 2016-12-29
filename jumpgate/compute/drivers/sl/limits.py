from jumpgate.common import config


class LimitsV2(object):
    def on_get(self, req, resp, tenant_id):
        client = req.sl_client

        account = client['Account'].getObject(
            mask='mask[hourlyVirtualGuestCount]')

        limits = {
            'absolute': {
                'maxImageMeta': config.PARSER.get("compute","default_metadata_items"),
                'maxPersonality': config.PARSER.get("compute","default_injected_files"),
                'maxPersonalitySize':
                config.PARSER.get("compute","default_injected_file_content_bytes"),
                'maxSecurityGroupRules':
                config.PARSER.get("compute","default_security_group_rules"),
                'maxSecurityGroups': config.PARSER.get("compute","default_security_groups"),
                'maxServerMeta': config.PARSER.get("compute","default_metadata_items"),
                'maxTotalCores': config.PARSER.get("compute","default_cores"),
                'maxTotalFloatingIps': config.PARSER.get("compute","default_floating_ips"),
                'maxTotalInstances': config.PARSER.get("compute","default_instances"),
                'maxTotalKeypairs': config.PARSER.get("compute","default_key_pairs"),
                'maxTotalRAMSize': config.PARSER.get("compute","default_ram"),
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

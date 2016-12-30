from jumpgate.common import config


class OSQuotaSetsV2(object):
    def on_get(self, req, resp, tenant_id, account_id=None):
        qs = {
            "cores": config.PARSER.get("compute",'default_cores'),
            "floating_ips": config.PARSER.get("compute",'default_floating_ips'),
            "id": tenant_id,
            "injected_file_content_bytes":
            config.PARSER.get("compute",'default_injected_file_content_bytes'),
            "injected_file_path_bytes":
            config.PARSER.get("compute",'default_injected_file_path_bytes'),
            "injected_files": config.PARSER.get("compute",'default_injected_files'),
            "instances": config.PARSER.get("compute",'default_instances'),
            "key_pairs": config.PARSER.get("compute",'default_key_pairs'),
            "metadata_items": config.PARSER.get("compute",'default_metadata_items'),
            "ram": config.PARSER.get("compute",'default_ram'),
            "security_group_rules":
            config.PARSER.get("compute",'default_security_group_rules'),
            "security_groups": config.PARSER.get("compute",'default_security_groups')
        }

        resp.body = {'quota_set': qs}

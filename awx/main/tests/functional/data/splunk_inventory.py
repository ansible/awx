#!/usr/bin/env python

# Python
import json
import optparse
import sys

inventory_dict = {
    "AWS Prod": {
        "children": [
            "security_group_tower",
            "tag_Role_cluster-master",
            "type_c3_2xlarge",
            "tag_Role_license-master",
            "tag_whisper_version_SEC-1639-20140414T1539-WR_17_HF3",
            "tag_Name_trial640_-_idx3",
            "tag_FQDN_sh1_trial614_splunkcloud_com",
            "security_group_finra_lm",
            "key_infra_trial605",
            "key_infra_trial607",
            "key_infra_trial606",
            "tag_FQDN_idx2_trial647_splunkcloud_com",
            "key_infra_trial609",
            "tag_Name_trial635_-_sh1",
            "tag_Name_poc4_-_idx1",
            "tag_Name_poc4_-_idx3",
            "tag_Name_poc4_-_idx2",
            "tag_Stack_mregan",
            "tag_stack_version_SR_8_HF1",
            "tag_FQDN_c0m1_mregan_splunkcloud_com",
            "key_infra_mregan",
            "tag_Name_mregan_-_c0m1",
            "tag_customer_type_dev",
            "tag_Ticket_CO-546",
            "tag_whisper_version_99",
            "tag_Role_search-head",
            "tag_customer_type_Dev",
            "key_infra_CO-920",
            "tag_Name_CO-920_-_lm1",
            "tag_FQDN_lm1_CO-920_splunkcloud_com",
            "tag_Stack_CO-920",
            "tag_Name_skynet_-_idx5",
            "tag_FQDN_idx5_skynet_splunkcloud_com",
            "tag_Name_skynet_-_idx6",
            "tag_FQDN_idx6_skynet_splunkcloud_com",
            "tag_customer_type_POC",
            "us-east-1c",
            "tag_Name_skynet_-_idx4",
            "tag_FQDN_idx4_skynet_splunkcloud_com",
            "tag_BuildUser_Mike_Regan",
            "tag_Name_skynet_-_idx3",
            "tag_FQDN_idx3_skynet_splunkcloud_com",
            "tag_Name_skynet_-_idx1",
            "tag_FQDN_idx1_skynet_splunkcloud_com",
            "tag_Name_skynet_-_idx2",
            "tag_FQDN_idx2_skynet_splunkcloud_com",
            "security_group_skynet",
            "tag_Stack_skynet",
            "key_infra_skynet",
            "tag_customer_type_Customer",
            "type_m2_4xlarge",
            "us-east-1b",
            "security_group_default",
            "us-east-1",
            "tag_whisper_version_SEC-1518-20140319T1154-WR_17_HF2",
            "ec2",
            "tag_Role_indexer",
            "us-east-1a",
            "tag_stackmakr_version_SEC-1553-20140326T1633-SR_8_HF1",
            "tag_Name_CO-920_-_c0m1",
            "tag_FQDN_c0m1_CO-920_splunkcloud_com",
            "tag_Name_splunk-sfdc_-_lm1",
            "tag_FQDN_lm1_splunk-sfdc_splunkcloud_com",
            "key_infra_splunk-sfdc",
            "tag_Name_splunk-sfdc_-_c0m1",
            "tag_FQDN_idx3_splunk-sfdc_splunkcloud_com",
            "tag_FQDN_idx1_splunk-sfdc_splunkcloud_com",
            "tag_FQDN_idx2_splunk-sfdc_splunkcloud_com",
            "tag_BuildUser_bwong",
            "tag_FQDN_idx2_CO-920_splunkcloud_com",
            "tag_Name_CO-920_-_idx2",
            "tag_Name_CO-920_-_idx3",
            "security_group_splunk-sfdc",
            "tag_Stack_splunk-sfdc",
            "tag_Name_splunk-sfdc_-_idx1",
            "tag_Ticket_CO-915",
            "tag_Name_splunk-sfdc_-_idx2",
            "tag_Name_splunk-sfdc_-_idx3",
            "tag_FQDN_c0m1_splunk-sfdc_splunkcloud_com",
            "tag_Name_CO-920_-_sh1",
            "tag_Name_CO-920_-_idx1",
            "tag_FQDN_idx1_CO-920_splunkcloud_com",
            "tag_FQDN_sh1_splunk-sfdc_splunkcloud_com",
            "tag_Name_splunk-sfdc_-_sh1",
            "tag_FQDN_idx1_prod-monitor-red_splunkcloud_com",
            "tag_Stack_prod-monitor-red",
            "tag_Name_prod-monitor-red_-_sh1",
            "tag_Name_prod-monitor-red_-_c0m1",
            "tag_FQDN_idx3_CO-920_splunkcloud_com",
            "tag_FQDN_sh1_CO-920_splunkcloud_com",
            "type_m1_xlarge",
            "tag_Ticket_CO-920",
            "tag_stackmakr_version_9109",
            "key_infra_prod-monitor-red",
            "tag_Name_prod-monitor-red_-_idx3",
            "tag_FQDN_idx2_prod-monitor-red_splunkcloud_com",
            "tag_Name_trial629_-_lm1",
            "security_group_mckesson_sh",
            "tag_FQDN_c0m1_trial617_splunkcloud_com",
            "tag_Name_trial623_-_c0m1",
            "tag_Name_poc2_-_lm1",
            "tag_FQDN_lm1_trial619_splunkcloud_com",
            "tag_FQDN_lm1_trial628_splunkcloud_com",
            "tag_FQDN_c0m1_trial618_splunkcloud_com",
            "tag_FQDN_ops-red-exec01_stackmakr-ops-red_splunkcloud_com",
            "tag_Name_trial633_-_lm1",
            "tag_Name_trial636_-_lm1",
            "tag_Name_trial641_-_c0m1",
            "tag_Name_intermedia_-_c0m1",
            "tag_Name_trial611_-_c0m1",
            "tag_Name_lyft_-_c0m1",
            "tag_Name_idexx_-_lm1",
            "tag_FQDN_lm1_trial640_splunkcloud_com",
            "tag_FQDN_c0m1_funtomic-prod_splunkcloud_com",
            "tag_FQDN_lm1_gilt_splunkcloud_com",
            "tag_FQDN_c0m1_lyft_splunkcloud_com",
            "tag_FQDN_lm1_trial647_splunkcloud_com",
            "tag_Name_trial636_-_c0m1",
            "tag_FQDN_lm1_trial642_splunkcloud_com",
            "tag_Name_poc3_-_c0m1",
            "tag_FQDN_lm1_trial625_splunkcloud_com",
            "tag_Name_mckesson_-_c0m1",
            "tag_FQDN_c0m1_trial612_splunkcloud_com",
            "tag_Name_trial629_-_c0m1",
            "tag_Name_sonos_-_lm1",
            "tag_FQDN_c0m1_k14_splunkcloud_com",
            "tag_Name_mregan_-_lm1",
            "tag_FQDN_c0m1_trial614_splunkcloud_com",
            "tag_Name_motionsoft_-_lm1",
            "tag_FQDN_lm1_intermedia_splunkcloud_com",
            "tag_Name_trial630_-_lm1",
            "tag_Name_mregan_-_idx1",
            "tag_Name_trial617_-_c0m1",
            "tag_Name_mregan_-_idx3",
            "tag_Name_mregan_-_idx2",
            "tag_FQDN_c0m1_trial640_splunkcloud_com",
            "tag_FQDN_lm1_funtomic-prod_splunkcloud_com",
            "tag_Name_trial635_-_lm1",
            "tag_FQDN_c0m1_trial625_splunkcloud_com",
            "tag_customer_type_Test",
            "tag_Name_prod-monitor-red_-_idx2",
            "tag_Name_prod-monitor-red_-_idx1",
            "tag_Name_defensenet_-_lm1",
            "tag_Name_trial640_-_lm1",
            "tag_Name_backupify_-_lm1",
            "tag_Name_mindtouch_-_lm1",
            "tag_FQDN_sh2_skynet_splunkcloud_com",
            "tag_FQDN_c0m1_trial630_splunkcloud_com",
            "tag_FQDN_c0m1_mindtouch_splunkcloud_com",
            "tag_FQDN_lm1_trial623_splunkcloud_com",
            "tag_FQDN_lm1_defensenet_splunkcloud_com",
            "tag_Name_trial619_-_c0m1",
            "tag_FQDN_lm1_trial637_splunkcloud_com",
            "tag_Name_trial643_-_lm1",
            "tag_FQDN_lm1_trial613_splunkcloud_com",
            "tag_FQDN_lm1_trial620_splunkcloud_com",
            "tag_Name_trial628_-_c0m1",
            "tag_FQDN_lm1_trial607_splunkcloud_com",
            "tag_FQDN_lm1_trial609_splunkcloud_com",
            "tag_FQDN_lm1_trial629_splunkcloud_com",
            "tag_FQDN_lm1_trial635_splunkcloud_com",
            "tag_FQDN_lm1_mregan_splunkcloud_com",
            "tag_Name_climate_-_c0m1",
            "tag_FQDN_c0m1_poc4_splunkcloud_com",
            "tag_FQDN_c0m1_trial631_splunkcloud_com",
            "tag_FQDN_lm1_spm1_splunkcloud_com",
            "tag_FQDN_c0m1_trial643_splunkcloud_com",
            "tag_Name_skynet_-_sh1",
            "tag_FQDN_lm1_trial641_splunkcloud_com",
            "tag_Name_trial640_-_c0m1",
            "tag_Name_spm1_-_lm1",
            "tag_FQDN_idx3_prod-monitor-red_splunkcloud_com",
            "tag_FQDN_idx2_mregan_splunkcloud_com",
            "tag_FQDN_c0m1_trial615_splunkcloud_com",
            "tag_Name_sonos_-_c0m1",
            "tag_FQDN_ops-red-exec02_stackmakr-ops-red_splunkcloud_com",
            "tag_FQDN_c0m1_trial644_splunkcloud_com",
            "tag_Name_trial622_-_lm1",
            "tag_FQDN_c0m1_trial620_splunkcloud_com",
            "tag_Name_trial613_-_lm1",
            "tag_FQDN_lm1_trial644_splunkcloud_com",
            "tag_Name_trial639_-_c0m1",
            "tag_FQDN_c0m1_poc3_splunkcloud_com",
            "tag_Name_climate_-_lm1",
            "tag_FQDN_lm1_white-ops_splunkcloud_com",
            "tag_FQDN_lm1_trial630_splunkcloud_com",
            "tag_FQDN_c0m1_idexx_splunkcloud_com",
            "tag_FQDN_c0m1_intermedia_splunkcloud_com",
            "tag_Name_trial616_-_c0m1",
            "tag_FQDN_lm1_idexx_splunkcloud_com",
            "tag_FQDN_c0m1_motionsoft_splunkcloud_com",
            "tag_FQDN_lm1_trial611_splunkcloud_com",
            "tag_Name_intermedia_-_lm1",
            "tag_Name_backupify_-_c0m1",
            "tag_Name_trial607_-_lm1",
            "tag_FQDN_c0m1_trial629_splunkcloud_com",
            "tag_FQDN_lm1_trial616_splunkcloud_com",
            "tag_FQDN_c0m1_poc2_splunkcloud_com",
            "tag_Name_skynet_-_sh2",
            "tag_Name_skynet_-_sh3",
            "tag_Name_trial634_-_lm1",
            "tag_Name_take2_-_c0m1",
            "tag_FQDN_c0m1_trial613_splunkcloud_com",
            "tag_Name_trial637_-_c0m1",
            "tag_FQDN_c0m1_trial623_splunkcloud_com",
            "tag_Name_trial612_-_lm1",
            "tag_FQDN_c0m1_trial637_splunkcloud_com",
            "tag_FQDN_c0m1_trial639_splunkcloud_com",
            "tag_FQDN_c0m1_trial605_splunkcloud_com",
            "tag_Name_trial633_-_c0m1",
            "tag_Name_trial607_-_c0m1",
            "tag_FQDN_lm1_backupify_splunkcloud_com",
            "tag_FQDN_c0m1_climate_splunkcloud_com",
            "tag_FQDN_lm1_poc3_splunkcloud_com",
            "tag_Name_trial606_-_c0m1",
            "tag_FQDN_lm1_poc1_splunkcloud_com",
            "tag_FQDN_lm1_trial614_splunkcloud_com",
            "tag_Name_gilt_-_c0m1",
            "tag_FQDN_lm1_trial626_splunkcloud_com",
            "tag_Name_stackmakr-ops-red_-_jenkins01",
            "tag_FQDN_c0m1_trial619_splunkcloud_com",
            "tag_Name_mindtouch_-_c0m1",
            "tag_Name_trial644_-_c0m1",
            "tag_FQDN_c0m1_white-ops_splunkcloud_com",
            "tag_FQDN_c0m1_trial609_splunkcloud_com",
            "tag_Name_trial634_-_c0m1",
            "tag_FQDN_c0m1_trial647_splunkcloud_com",
            "tag_Name_trial626_-_lm1",
            "tag_FQDN_c0m1_backupify_splunkcloud_com",
            "tag_Name_stackmakr-ops-red_-_ops-red-exec01",
            "tag_Name_trial625_-_c0m1",
            "tag_FQDN_lm1_trial643_splunkcloud_com",
            "tag_FQDN_lm1_trial627_splunkcloud_com",
            "tag_Name_trial643_-_c0m1",
            "tag_FQDN_c0m1_sonos_splunkcloud_com",
            "tag_FQDN_lm1_poc2_splunkcloud_com",
            "tag_FQDN_lm1_skynet_splunkcloud_com",
            "tag_FQDN_lm1_sonos_splunkcloud_com",
            "tag_FQDN_c0m1_trial642_splunkcloud_com",
            "tag_FQDN_c0m1_trial645_splunkcloud_com",
            "tag_FQDN_lm1_trial646_splunkcloud_com",
            "tag_FQDN_c0m1_trial627_splunkcloud_com",
            "tag_Name_trial647_-_lm1",
            "tag_Name_k14_-_lm1",
            "tag_Name_trial625_-_lm1",
            "tag_Name_trial627_-_lm1",
            "tag_Name_white-ops_-_c0m1",
            "tag_Ticket_CO-895",
            "tag_FQDN_lm1_trial612_splunkcloud_com",
            "tag_FQDN_lm1_anaplan_splunkcloud_com",
            "tag_FQDN_c0m1_trial641_splunkcloud_com",
            "tag_Name_trial606_-_lm1",
            "tag_Name_finra_-_sh2",
            "tag_Name_trial616_-_lm1",
            "tag_Name_trial641_-_lm1",
            "tag_FQDN_c0m1_trial626_splunkcloud_com",
            "tag_FQDN_sh3_skynet_splunkcloud_com",
            "tag_FQDN_idx3_mregan_splunkcloud_com",
            "tag_Name_trial620_-_c0m1",
            "tag_Name_trial635_-_c0m1",
            "tag_FQDN_lm1_trial633_splunkcloud_com",
            "tag_Name_trial638_-_lm1",
            "tag_FQDN_c0m1_trial616_splunkcloud_com",
            "tag_Name_trial631_-_lm1",
            "tag_Name_trial614_-_lm1",
            "type_t1_micro",
            "tag_Name_trial615_-_lm1",
            "tag_Name_stackmakr-ops-red_-_ops-red-exec02",
            "tag_FQDN_lm1_trial634_splunkcloud_com",
            "tag_FQDN_lm1_trial639_splunkcloud_com",
            "tag_Name_trial642_-_lm1",
            "tag_Name_stackmakr-ops-red_-_ops-red-exec04",
            "tag_FQDN_c0m1_trial634_splunkcloud_com",
            "tag_FQDN_lm1_trial621_splunkcloud_com",
            "tag_Name_gilt_-_lm1",
            "tag_FQDN_lm1_motionsoft_splunkcloud_com",
            "tag_FQDN_c0m1_spm1_splunkcloud_com",
            "tag_Name_skynet_-_c0m1",
            "tag_FQDN_c0m1_trial606_splunkcloud_com",
            "tag_FQDN_c0m1_trial635_splunkcloud_com",
            "tag_Name_trial645_-_c0m1",
            "tag_Name_mindtouch_-_sh2",
            "tag_Name_trial613_-_c0m1",
            "tag_Name_take2_-_lm1",
            "tag_FQDN_c0m1_trial628_splunkcloud_com",
            "tag_FQDN_sh1_mregan_splunkcloud_com",
            "tag_Name_trial605_-_c0m1",
            "tag_Name_trial644_-_lm1",
            "tag_Name_trial619_-_lm1",
            "tag_Name_defensenet_-_c0m1",
            "tag_FQDN_lm1_mckesson_splunkcloud_com",
            "tag_Name_trial646_-_lm1",
            "tag_Name_poc4_-_lm1",
            "tag_Name_poc3_-_lm1",
            "tag_FQDN_c0m1_trial622_splunkcloud_com",
            "tag_Name_trial609_-_lm1",
            "tag_FQDN_lm1_climate_splunkcloud_com",
            "tag_FQDN_c0m1_defensenet_splunkcloud_com",
            "tag_Name_trial647_-_c0m1",
            "tag_FQDN_lm1_trial605_splunkcloud_com",
            "tag_FQDN_lm1_trial645_splunkcloud_com",
            "tag_Name_trial637_-_lm1",
            "tag_FQDN_lm1_trial606_splunkcloud_com",
            "tag_FQDN_c0m1_poc1_splunkcloud_com",
            "tag_FQDN_c0m1_gilt_splunkcloud_com",
            "tag_FQDN_idx1_mregan_splunkcloud_com",
            "tag_Name_lyft_-_lm1",
            "tag_FQDN_c0m1_skynet_splunkcloud_com",
            "tag_FQDN_lm1_trial617_splunkcloud_com",
            "tag_Name_anaplan_-_c0m1",
            "tag_Name_trial631_-_c0m1",
            "tag_Name_poc4_-_c0m1",
            "tag_Name_motionsoft_-_c0m1",
            "tag_FQDN_c0m1_trial633_splunkcloud_com",
            "tag_Name_trial646_-_c0m1",
            "tag_FQDN_lm1_take2_splunkcloud_com",
            "tag_Name_idexx_-_c0m1",
            "tag_FQDN_lm1_lyft_splunkcloud_com",
            "tag_Name_trial626_-_c0m1",
            "tag_FQDN_c0m1_trial611_splunkcloud_com",
            "tag_Name_trial627_-_c0m1",
            "tag_Name_mregan_-_sh1",
            "tag_FQDN_c0m1_trial646_splunkcloud_com",
            "tag_Name_trial632_-_lm1",
            "tag_FQDN_c0m1_anaplan_splunkcloud_com",
            "tag_Name_trial615_-_c0m1",
            "tag_Name_poc1_-_c0m1",
            "tag_Name_trial621_-_lm1",
            "tag_FQDN_lm1_trial636_splunkcloud_com",
            "tag_Name_skynet_-_lm1",
            "tag_Stack_stackmakr-ops-red",
            "tag_Name_trial630_-_c0m1",
            "tag_Name_prod_infra_test",
            "tag_FQDN_c0m1_trial636_splunkcloud_com",
            "tag_Name_trial612_-_c0m1",
            "tag_Name_trial618_-_c0m1",
            "tag_Name_trial632_-_c0m1",
            "tag_Name_trial645_-_lm1",
            "tag_Name_trial617_-_lm1",
            "tag_Name_k14_-_c0m1",
            "tag_FQDN_lm1_trial622_splunkcloud_com",
            "tag_Name_trial609_-_c0m1",
            "tag_FQDN_jenkins01_stackmakr-ops-red_splunkcloud_com",
            "tag_Name_funtomic-prod_-_lm1",
            "tag_FQDN_sh2_mindtouch_splunkcloud_com",
            "tag_Name_trial638_-_c0m1",
            "tag_FQDN_lm1_trial631_splunkcloud_com",
            "tag_Name_white-ops_-_lm1",
            "tag_Name_trial620_-_lm1",
            "tag_FQDN_sh1_skynet_splunkcloud_com",
            "tag_FQDN_c0m1_mckesson_splunkcloud_com",
            "tag_FQDN_c0m1_trial607_splunkcloud_com",
            "tag_Name_poc1_-_lm1",
            "tag_Name_anaplan_-_lm1",
            "tag_FQDN_lm1_trial632_splunkcloud_com",
            "tag_Name_spm1_-_c0m1",
            "tag_Name_trial642_-_c0m1",
            "tag_FQDN_c0m1_take2_splunkcloud_com",
            "tag_Name_poc2_-_c0m1",
            "tag_Name_trial614_-_c0m1",
            "tag_Name_stackmakr-ops-red_-_ops-red-exec03",
            "tag_FQDN_lm1_trial618_splunkcloud_com",
            "tag_FQDN_lm1_mindtouch_splunkcloud_com",
            "tag_FQDN_lm1_k14_splunkcloud_com",
            "tag_Name_trial622_-_c0m1",
            "security_group_stackmakr",
            "tag_Name_trial639_-_lm1",
            "tag_Name_trial621_-_c0m1",
            "tag_Name_funtomic-prod_-_c0m1",
            "tag_Name_trial605_-_lm1",
            "tag_FQDN_lm1_trial615_splunkcloud_com",
            "tag_Name_trial623_-_lm1",
            "tag_Name_trial611_-_lm1",
            "key_infra_sonos",
            "tag_FQDN_c0m1_trial621_splunkcloud_com",
            "tag_FQDN_lm1_poc4_splunkcloud_com",
            "tag_Name_trial618_-_lm1",
            "tag_FQDN_lm1_trial638_splunkcloud_com",
            "tag_FQDN_sh2_finra_splunkcloud_com",
            "tag_FQDN_c0m1_trial638_splunkcloud_com",
            "tag_Name_mckesson_-_lm1",
            "tag_FQDN_c0m1_trial632_splunkcloud_com",
            "tag_Name_trial628_-_lm1",
            "tag_Ticket_CO-749",
            "tag_Name_trial631_-_idx3",
            "tag_Name_trial612_-_idx1",
            "tag_Ticket_CO-807",
            "key_infra_trial617",
            "key_infra_trial614",
            "key_infra_trial615",
            "key_infra_trial612",
            "tag_FQDN_idx3_funtomic-prod_splunkcloud_com",
            "key_infra_trial611",
            "tag_FQDN_idx3_mckesson_splunkcloud_com",
            "tag_Name_trial614_-_idx1",
            "tag_FQDN_idx2_trial606_splunkcloud_com",
            "tag_Name_trial614_-_idx3",
            "key_infra_trial618",
            "key_infra_trial619",
            "tag_FQDN_idx2_trial613_splunkcloud_com",
            "tag_FQDN_idx3_trial630_splunkcloud_com",
            "key_infra_trial626",
            "tag_FQDN_sh1_trial613_splunkcloud_com",
            "tag_FQDN_idx3_trial643_splunkcloud_com",
            "tag_Name_defensenet_-_sh1",
            "tag_Stack_defensenet",
            "tag_FQDN_idx1_trial628_splunkcloud_com",
            "tag_FQDN_idx1_trial634_splunkcloud_com",
            "tag_Stack_trial605",
            "tag_Ticket_CO-279",
            "tag_FQDN_sh1_trial620_splunkcloud_com",
            "security_group_trials",
            "tag_FQDN_idx1_trial636_splunkcloud_com",
            "tag_FQDN_idx3_trial626_splunkcloud_com",
            "tag_FQDN_sh1_trial644_splunkcloud_com",
            "tag_FQDN_c0m1_poc5_splunkcloud_com",
            "tag_Ticket_CO-478",
            "tag_FQDN_sh1_trial636_splunkcloud_com",
            "tag_Name_trial646_-_sh1",
            "key_infra_spm1",
            "tag_Name_trial636_-_sh1",
            "tag_Name_trial611_-_idx2",
            "tag_Name_trial611_-_idx1",
            "tag_Name_trial609_-_idx2",
            "tag_FQDN_idx1_trial619_splunkcloud_com",
            "tag_Name_spm1_-_idx2",
            "tag_Name_spm1_-_idx3",
            "tag_FQDN_idx3_k14_splunkcloud_com",
            "tag_Name_spm1_-_idx1",
            "tag_Name_trial606_-_sh1",
            "tag_Stack_trial629",
            "key_infra_climate",
            "tag_Ticket_CO-493",
            "tag_FQDN_idx2_trial636_splunkcloud_com",
            "tag_FQDN_idx3_trial614_splunkcloud_com",
            "tag_FQDN_sh1_trial634_splunkcloud_com",
            "tag_Name_idexx_-_idx3",
            "tag_FQDN_idx3_trial645_splunkcloud_com",
            "tag_Name_trial631_-_sh1",
            "tag_FQDN_idx2_poc3_splunkcloud_com",
            "tag_FQDN_idx3_lyft_splunkcloud_com",
            "tag_FQDN_sh1_defensenet_splunkcloud_com",
            "tag_Name_gilt_-_idx4",
            "tag_FQDN_idx2_trial631_splunkcloud_com",
            "tag_FQDN_idx3_trial615_splunkcloud_com",
            "tag_Stack_trial617",
            "tag_Name_trial642_-_sh1",
            "tag_Stack_trial615",
            "tag_Stack_trial614",
            "tag_Stack_trial613",
            "tag_Stack_trial611",
            "tag_FQDN_idx2_trial634_splunkcloud_com",
            "tag_Stack_trial619",
            "tag_Stack_trial618",
            "tag_Name_trial639_-_idx1",
            "tag_FQDN_idx8_intermedia_splunkcloud_com",
            "tag_Name_trial639_-_idx3",
            "tag_Name_trial639_-_idx2",
            "tag_FQDN_idx3_gilt_splunkcloud_com",
            "tag_FQDN_idx6_intermedia_splunkcloud_com",
            "tag_FQDN_idx3_trial607_splunkcloud_com",
            "security_group_motionsoft",
            "tag_Ticket_CO-653",
            "tag_FQDN_idx2_trial612_splunkcloud_com",
            "tag_Ticket_CO-651",
            "tag_Ticket_CO-650",
            "tag_Ticket_CO-655",
            "tag_FQDN_sh1_trial612_splunkcloud_com",
            "tag_FQDN_idx1_poc2_splunkcloud_com",
            "tag_FQDN_idx4_intermedia_splunkcloud_com",
            "tag_Stack_intermedia",
            "tag_FQDN_idx2_poc4_splunkcloud_com",
            "tag_FQDN_sh1_trial632_splunkcloud_com",
            "security_group_trial611",
            "tag_Name_poc3_-_sh1",
            "security_group_NAT",
            "tag_Name_spm1_-_sh1",
            "tag_FQDN_idx2_motionsoft_splunkcloud_com",
            "key_infra_backupify",
            "tag_Name_poc5_-_idx2",
            "tag_Name_poc5_-_idx3",
            "tag_Name_poc5_-_idx1",
            "security_group_sonos",
            "tag_Name_white-ops_-_sh1",
            "key_infra_trial628",
            "tag_FQDN_sh1_trial617_splunkcloud_com",
            "key_infra_trial641",
            "key_infra_trial640",
            "key_infra_trial642",
            "key_infra_trial645",
            "key_infra_trial644",
            "key_infra_trial647",
            "key_infra_trial646",
            "tag_FQDN_idx2_idexx_splunkcloud_com",
            "tag_FQDN_sh1_trial618_splunkcloud_com",
            "tag_FQDN_lm1_marriott_splunkcloud_com",
            "tag_Name_poc3_-_idx1",
            "tag_Name_poc3_-_idx2",
            "tag_Name_poc3_-_idx3",
            "tag_Stack_poc2",
            "security_group_mindtouch",
            "tag_Stack_motionsoft",
            "security_group_take2",
            "key_infra_gilt",
            "tag_FQDN_idx3_trial642_splunkcloud_com",
            "tag_FQDN_idx1_trial611_splunkcloud_com",
            "tag_FQDN_sh1_trial626_splunkcloud_com",
            "security_group_chef",
            "tag_Name_trial641_-_idx2",
            "tag_Name_trial641_-_idx3",
            "tag_Name_trial641_-_idx1",
            "tag_Ticket_CO-874",
            "tag_Name_poc2_-_sh1",
            "tag_Name_trial617_-_sh1",
            "tag_Name_trial609_-_sh1",
            "tag_Name_sonos_-_idx6",
            "tag_Name_sonos_-_idx4",
            "tag_Name_sonos_-_idx5",
            "key_infra_white-ops",
            "tag_Name_sonos_-_idx3",
            "tag_Name_sonos_-_idx1",
            "tag_Name_sonos_-_idx2",
            "tag_Name_trial628_-_sh1",
            "tag_FQDN_idx3_trial646_splunkcloud_com",
            "tag_Name_trial631_-_idx1",
            "tag_FQDN_idx3_poc1_splunkcloud_com",
            "tag_Name_trial612_-_idx3",
            "tag_Name_trial619_-_idx3",
            "tag_Name_trial616_-_sh1",
            "tag_Name_trial613_-_idx1",
            "tag_Name_trial613_-_idx3",
            "tag_FQDN_idx2_trial629_splunkcloud_com",
            "tag_FQDN_idx1_trial612_splunkcloud_com",
            "tag_Name_trial631_-_idx2",
            "tag_Ticket_CO-194",
            "tag_Name_trial619_-_idx1",
            "tag_FQDN_idx2_trial620_splunkcloud_com",
            "tag_FQDN_sh1_trial647_splunkcloud_com",
            "tag_Name_finra_-_lm1",
            "tag_FQDN_idx1_trial630_splunkcloud_com",
            "tag_FQDN_idx3_trial632_splunkcloud_com",
            "tag_FQDN_idx1_trial641_splunkcloud_com",
            "security_group_trial621",
            "tag_FQDN_idx3_trial636_splunkcloud_com",
            "tag_FQDN_sh1_sonos_splunkcloud_com",
            "tag_FQDN_sh1_backupify_splunkcloud_com",
            "tag_FQDN_idx1_trial633_splunkcloud_com",
            "tag_Name_poc2_-_idx1",
            "tag_FQDN_idx2_trial614_splunkcloud_com",
            "tag_FQDN_idx3_trial639_splunkcloud_com",
            "tag_Ticket_CO-562",
            "tag_Name_marriott_-_c0m1",
            "tag_Name_trial623_-_sh1",
            "tag_FQDN_idx4_finra_splunkcloud_com",
            "tag_Name_trial625_-_idx3",
            "tag_FQDN_sh1_idexx_splunkcloud_com",
            "security_group_defensenet",
            "tag_FQDN_idx3_trial612_splunkcloud_com",
            "tag_Name_trial647_-_sh1",
            "key_infra_take2",
            "tag_FQDN_sh1_climate_splunkcloud_com",
            "tag_FQDN_sh1_spm1_splunkcloud_com",
            "tag_FQDN_idx3_trial633_splunkcloud_com",
            "tag_FQDN_idx2_take2_splunkcloud_com",
            "key_infra_idexx",
            "tag_FQDN_idx2_mckesson_splunkcloud_com",
            "key_infra_trial616",
            "tag_Name_trial646_-_idx3",
            "tag_Name_trial646_-_idx2",
            "tag_Name_trial646_-_idx1",
            "tag_FQDN_idx2_trial605_splunkcloud_com",
            "security_group_k14",
            "tag_Stack_mckesson",
            "tag_FQDN_sh1_poc5_splunkcloud_com",
            "security_group_gilt",
            "tag_Role_jenkins-executor",
            "tag_FQDN_idx4_gilt_splunkcloud_com",
            "tag_FQDN_sh1_trial625_splunkcloud_com",
            "tag_FQDN_idx1_trial640_splunkcloud_com",
            "key_infra_stackmakr-ops-blue",
            "key_infra_trial613",
            "tag_FQDN_idx1_trial607_splunkcloud_com",
            "tag_FQDN_idx1_mindtouch_splunkcloud_com",
            "tag_Ticket_CO-330",
            "tag_FQDN_idx1_trial620_splunkcloud_com",
            "tag_Name_trial607_-_sh1",
            "tag_FQDN_idx2_trial637_splunkcloud_com",
            "tag_Name_trial622_-_idx1",
            "tag_Stack_trial628",
            "tag_Name_trial622_-_idx2",
            "tag_Stack_trial626",
            "tag_Stack_trial627",
            "tag_Stack_trial622",
            "tag_Stack_trial623",
            "tag_Name_trial628_-_idx1",
            "tag_Stack_trial621",
            "tag_Name_intermedia_-_idx7",
            "tag_Name_intermedia_-_idx6",
            "tag_Name_intermedia_-_idx5",
            "tag_Name_intermedia_-_idx4",
            "tag_FQDN_idx1_trial623_splunkcloud_com",
            "tag_Name_intermedia_-_idx2",
            "tag_Name_intermedia_-_idx1",
            "tag_FQDN_idx1_trial621_splunkcloud_com",
            "tag_Name_intermedia_-_idx8",
            "tag_Name_trial634_-_sh1",
            "tag_FQDN_idx2_trial642_splunkcloud_com",
            "tag_Name_trial618_-_sh1",
            "tag_Ticket_CO-549",
            "tag_FQDN_sh1_trial622_splunkcloud_com",
            "tag_Name_mckesson_-_idx1",
            "tag_FQDN_idx1_white-ops_splunkcloud_com",
            "tag_Name_mckesson_-_idx3",
            "type_hs1_8xlarge",
            "tag_Name_trial612_-_sh1",
            "tag_FQDN_idx1_trial638_splunkcloud_com",
            "tag_Name_lyft_-_idx2",
            "tag_Name_trial629_-_idx1",
            "tag_Name_trial629_-_idx2",
            "key_infra_motionsoft",
            "security_group_trial636",
            "tag_FQDN_sh1_trial643_splunkcloud_com",
            "tag_FQDN_idx3_finra_splunkcloud_com",
            "tag_FQDN_idx2_white-ops_splunkcloud_com",
            "tag_FQDN_idx1_anaplan_splunkcloud_com",
            "tag_FQDN_idx1_poc4_splunkcloud_com",
            "tag_Stack_zabbix",
            "tag_FQDN_idx3_trial605_splunkcloud_com",
            "tag_Name_trial614_-_sh1",
            "tag_Name_mckesson_-_idx2",
            "tag_Name_trial644_-_idx1",
            "tag_Name_trial644_-_idx3",
            "tag_Name_trial644_-_idx2",
            "tag_Name_trial612_-_idx2",
            "tag_Name_poc4_-_sh1",
            "tag_Name_security-test_-_sh1",
            "tag_FQDN_idx6_gilt_splunkcloud_com",
            "tag_BuildUser_Joped",
            "tag_FQDN_sh1_trial624_splunkcloud_com",
            "tag_Name_fidoplus_-_chef-sandbox-dev",
            "tag_FQDN_lm1_prod-monitor-red_splunkcloud_com",
            "tag_Name_prod-monitor-red_-_lm1",
            "key_infra_trial610",
            "security_group_chef_server",
            "tag_Name_trial624_-_idx2",
            "tag_FQDN_idx2_trial610_splunkcloud_com",
            "security_group_security-test_lm",
            "tag_FQDN_idx3_trial606_splunkcloud_com",
            "tag_Name_trial608_-_idx1",
            "tag_FQDN_sh1_prod-monitor-red_splunkcloud_com",
            "tag_FQDN_c0m1_prod-monitor-red_splunkcloud_com",
            "type_c1_medium",
            "tag_Stack_trial610",
            "tag_Ticket_CO-494",
            "tag_FQDN_idx1_sonos_splunkcloud_com",
            "tag_Name_idexx_-_idx2",
            "tag_Name_trial608_-_idx3",
            "tag_FQDN_idx2_security-test_splunkcloud_com",
            "tag_License_whisper-project-test",
            "tag_FQDN_idx1_trial624_splunkcloud_com",
            "tag_Name_chef_-_whisper",
            "security_group_security-test_idx",
            "key_infra_trial643",
            "security_group_fidoplus",
            "tag_Name_1sot",
            "tag_Name_security-test_-_lm1",
            "security_group_fido",
            "tag_FQDN_idx1_trial610_splunkcloud_com",
            "security_group_stackmakr-corp",
            "tag_Stack_fidoplus",
            "security_group_zabbix-client",
            "tag_Name_backupify_-_idx1",
            "tag_FQDN_idx1_backupify_splunkcloud_com",
            "security_group_trial622",
            "security_group_trial623",
            "security_group_trial620",
            "tag_Stack_trial624",
            "security_group_splunk-support",
            "tag_Stack_stackmakr-corp",
            "key_infra_trial608",
            "type_m1_large",
            "security_group_trial610",
            "tag_customer_type_Trial",
            "tag_Name_trial624_-_idx3",
            "security_group_jenkins-master",
            "security_group_ssh",
            "security_group_trial624",
            "tag_Name_trial610_-_idx2",
            "tag_Name_trial610_-_idx3",
            "tag_FQDN_c0m1_security-test_splunkcloud_com",
            "tag_Ticket_CO-640",
            "tag_Name_trial608_-_sh1",
            "security_group_stackmakr-ops-blue",
            "tag_Stack_fido",
            "tag_Name_stackmakr-corp_-_jenkins01",
            "tag_FQDN_idx2_trial608_splunkcloud_com",
            "tag_Name_trial610_-_idx1",
            "security_group_1sot",
            "tag_Role_chef_server",
            "tag_FQDN_idx2_trial624_splunkcloud_com",
            "tag_FQDN_idx3_trial624_splunkcloud_com",
            "tag_Stack_backupify",
            "tag_Name_fido_-_zabbix",
            "tag_FQDN_jenkins01_stackmakr-ops-blue_splunkcloud_com",
            "tag_Name_security-test_-_idx1",
            "tag_Name_security-test_-_idx2",
            "security_group_security-test",
            "tag_Stack_stackmakr-ops-blue",
            "tag_FQDN_chef-sandbox-dev_fidoplus_splunkwhisper_com",
            "tag_Name_stackmakr-corp_-_exec03",
            "security_group_stackmakr-service",
            "tag_Name_trial634_-_idx2",
            "tag_Name_trial634_-_idx3",
            "tag_Name_trial634_-_idx1",
            "security_group_security-test_sh",
            "tag_Name_trial624_-_sh1",
            "tag_Name_trial624_-_idx1",
            "tag_FQDN_idx2_anaplan_splunkcloud_com",
            "tag_FQDN_lm1_finra_splunkcloud_com",
            "tag_FQDN_chef-corp-dev_fidoplus_splunkwhisper_com",
            "tag_FQDN_sh1_trial608_splunkcloud_com",
            "tag_Stack_security-test",
            "security_group_stackmakr-corp_lm",
            "tag_Name_trial608_-_idx2",
            "key_infra_anaplan",
            "tag_Name_stackmakr-ops-blue_-_ops-blue-exec02",
            "tag_Name_stackmakr-ops-blue_-_ops-blue-exec01",
            "security_group_jenkins-executor",
            "tag_FQDN_idx1_trial608_splunkcloud_com",
            "tag_FQDN_exec03_stackmakr-corp_splunkwhisper_com",
            "tag_Name_stackmakr-ops-blue_-_jenkins01",
            "tag_Name_marriott_-_sh1",
            "tag_FQDN_idx2_mindtouch_splunkcloud_com",
            "tag_Name_defensenet_-_idx2",
            "security_group_nessus",
            "tag_Ticket_CO-638",
            "security_group_trial608",
            "security_group_stackmakr-corp_cm",
            "tag_FQDN_idx3_trial610_splunkcloud_com",
            "tag_FQDN_ops-blue-exec01_stackmakr-ops-blue_splunkcloud_com",
            "tag_Stack_trial608",
            "tag_FQDN_sh1_trial610_splunkcloud_com",
            "tag_FQDN_jenkins01_stackmakr-corp_splunkwhisper_com",
            "tag_Name_fidoplus_-_chef-corp-dev",
            "tag_Ticket_CO-654",
            "tag_FQDN_idx2_trial639_splunkcloud_com",
            "tag_FQDN_idx3_anaplan_splunkcloud_com",
            "tag_FQDN_ops-blue-exec02_stackmakr-ops-blue_splunkcloud_com",
            "tag_Name_security-test_-_c0m1",
            "key_infra_trial624",
            "tag_Ticket_CO-35",
            "security_group_security-test_cm",
            "tag_Name_nessus",
            "tag_FQDN_idx3_trial647_splunkcloud_com",
            "tag_FQDN_sh1_finra_splunkcloud_com",
            "tag_FQDN_idx1_security-test_splunkcloud_com",
            "tag_FQDN_sh1_security-test_splunkcloud_com",
            "tag_FQDN_lm1_security-test_splunkcloud_com",
            "tag_FQDN_idx3_trial608_splunkcloud_com",
            "tag_Name_trial610_-_sh1",
            "tag_Name_trial640_-_idx1",
            "tag_Name_trial620_-_idx3",
            "tag_Name_trial620_-_idx2",
            "tag_Name_trial620_-_idx1",
            "tag_FQDN_idx3_marriott_splunkcloud_com",
            "tag_FQDN_idx2_trial644_splunkcloud_com",
            "tag_FQDN_idx2_trial623_splunkcloud_com",
            "security_group_search-head",
            "security_group_idexx",
            "tag_Name_trial613_-_sh1",
            "tag_FQDN_idx1_climate_splunkcloud_com",
            "tag_FQDN_sh1_trial645_splunkcloud_com",
            "tag_Name_idexx_-_sh1",
            "tag_Name_trial633_-_sh1",
            "tag_FQDN_idx2_trial617_splunkcloud_com",
            "tag_Ticket_CO-398",
            "security_group_trial617",
            "security_group_trial616",
            "tag_FQDN_idx3_trial609_splunkcloud_com",
            "tag_FQDN_sh1_trial607_splunkcloud_com",
            "tag_FQDN_idx3_trial635_splunkcloud_com",
            "tag_Name_zabbix_-_zabbix1",
            "tag_FQDN_idx1_trial644_splunkcloud_com",
            "tag_Name_backupify_-_idx3",
            "tag_Name_climate_-_idx1",
            "tag_Name_climate_-_idx3",
            "tag_Name_climate_-_idx2",
            "tag_FQDN_sh1_trial631_splunkcloud_com",
            "tag_Name_trial630_-_idx2",
            "tag_FQDN_idx2_finra_splunkcloud_com",
            "tag_Ticket_CO-303",
            "tag_Name_trial630_-_idx1",
            "tag_FQDN_sh1_trial611_splunkcloud_com",
            "tag_Stack_finra",
            "key_infra_funtomic-prod",
            "tag_Stack_sonos",
            "tag_Name_poc5_-_sh1",
            "tag_Stack_poc5",
            "tag_Name_trial618_-_idx1",
            "tag_Name_trial618_-_idx2",
            "tag_Name_trial618_-_idx3",
            "tag_FQDN_idx1_trial626_splunkcloud_com",
            "key_infra_trial621",
            "tag_FQDN_sh1_white-ops_splunkcloud_com",
            "tag_FQDN_idx2_trial626_splunkcloud_com",
            "tag_FQDN_idx3_white-ops_splunkcloud_com",
            "tag_Name_gilt_-_idx2",
            "security_group_jenkins-blue",
            "tag_FQDN_idx3_trial616_splunkcloud_com",
            "tag_FQDN_idx1_lyft_splunkcloud_com",
            "tag_Name_finra_-_c0m1",
            "tag_FQDN_idx3_trial634_splunkcloud_com",
            "tag_FQDN_idx6_sonos_splunkcloud_com",
            "key_infra_finra",
            "tag_FQDN_idx3_spm1_splunkcloud_com",
            "tag_FQDN_sh1_trial615_splunkcloud_com",
            "key_infra_defensenet",
            "tag_Name_trial627_-_idx2",
            "tag_Name_trial627_-_idx3",
            "tag_FQDN_idx5_gilt_splunkcloud_com",
            "key_infra_lyft",
            "tag_FQDN_idx3_trial627_splunkcloud_com",
            "tag_Name_trial613_-_idx2",
            "tag_Name_trial627_-_idx1",
            "security_group__intermedia",
            "tag_FQDN_idx2_poc5_splunkcloud_com",
            "tag_Ticket_CO-635",
            "key_infra_marriott",
            "tag_Name_trial642_-_idx3",
            "tag_FQDN_idx7_intermedia_splunkcloud_com",
            "tag_Name_trial642_-_idx1",
            "tag_Ticket_CO-644",
            "tag_Ticket_CO-645",
            "tag_Ticket_CO-646",
            "tag_Ticket_CO-647",
            "tag_Ticket_CO-641",
            "tag_FQDN_idx3_poc5_splunkcloud_com",
            "tag_FQDN_idx1_take2_splunkcloud_com",
            "tag_FQDN_idx3_poc3_splunkcloud_com",
            "tag_Ticket_CO-648",
            "tag_Ticket_CO-649",
            "tag_FQDN_idx1_finra_splunkcloud_com",
            "tag_FQDN_idx1_marriott_splunkcloud_com",
            "tag_FQDN_idx4_sonos_splunkcloud_com",
            "tag_FQDN_sh1_trial635_splunkcloud_com",
            "tag_Role_jenkins-master",
            "tag_FQDN_idx1_trial617_splunkcloud_com",
            "tag_FQDN_idx3_poc4_splunkcloud_com",
            "tag_FQDN_idx3_trial619_splunkcloud_com",
            "tag_FQDN_idx1_spm1_splunkcloud_com",
            "tag_FQDN_idx3_trial622_splunkcloud_com",
            "tag_FQDN_sh1_poc2_splunkcloud_com",
            "tag_Name_sc-vpc-nat__subnet_3_",
            "tag_FQDN_c0m1_marriott_splunkcloud_com",
            "tag_FQDN_idx1_trial606_splunkcloud_com",
            "tag_Name_trial647_-_idx1",
            "tag_Name_trial647_-_idx2",
            "tag_Name_trial647_-_idx3",
            "tag_Name_trial615_-_idx3",
            "tag_Stack_trial645",
            "tag_FQDN_sh1_trial623_splunkcloud_com",
            "key_infra_mindtouch",
            "tag_Stack_idexx",
            "tag_Name_trial645_-_idx2",
            "tag_Name_trial645_-_idx3",
            "tag_Name_trial645_-_idx1",
            "key_infra_sc_nat",
            "security_group_finra_cm",
            "tag_Stack_mindtouch",
            "tag_Name_gilt_-_sh1",
            "tag_FQDN_idx1_trial622_splunkcloud_com",
            "tag_FQDN_idx3_trial620_splunkcloud_com",
            "tag_Ticket_CO-666",
            "tag_Name_k14_-_idx2",
            "tag_Name_k14_-_idx3",
            "tag_Name_trial621_-_idx2",
            "tag_Name_k14_-_idx1",
            "tag_Stack_spm1",
            "tag_FQDN_idx2_trial635_splunkcloud_com",
            "key_infra_poc4",
            "key_infra_poc1",
            "key_infra_poc3",
            "key_infra_poc2",
            "tag_FQDN_idx2_funtomic-prod_splunkcloud_com",
            "tag_FQDN_c0m1_finra_splunkcloud_com",
            "tag_Name_intermedia_-_sh1",
            "tag_FQDN_sh1_funtomic-prod_splunkcloud_com",
            "tag_FQDN_idx2_intermedia_splunkcloud_com",
            "tag_FQDN_sh1_trial642_splunkcloud_com",
            "tag_Name_trial622_-_sh1",
            "tag_FQDN_idx9_intermedia_splunkcloud_com",
            "tag_FQDN_idx1_idexx_splunkcloud_com",
            "security_group_spm1",
            "tag_FQDN_sh1_trial640_splunkcloud_com",
            "type_m1_medium",
            "tag_Name_backupify_-_sh1",
            "type_c3_4xlarge",
            "tag_Ticket_CO-637",
            "tag_FQDN_idx1_trial609_splunkcloud_com",
            "tag_Ticket_CO-636",
            "security_group_indexer",
            "tag_BuildUser_mloven",
            "tag_FQDN_idx2_backupify_splunkcloud_com",
            "tag_FQDN_idx5_sonos_splunkcloud_com",
            "tag_Name_trial643_-_idx1",
            "tag_Name_trial643_-_idx2",
            "tag_Name_trial643_-_idx3",
            "tag_FQDN_sh1_trial605_splunkcloud_com",
            "tag_Name_trial642_-_idx2",
            "tag_Name_trial632_-_sh1",
            "tag_Name_trial609_-_idx3",
            "tag_Ticket_CO-358",
            "tag_Name_trial609_-_idx1",
            "tag_Ticket_CO-296",
            "tag_FQDN_idx1_poc1_splunkcloud_com",
            "tag_FQDN_sh1_trial638_splunkcloud_com",
            "tag_FQDN_idx2_trial611_splunkcloud_com",
            "tag_Ticket_CO-351",
            "tag_Stack_white-ops",
            "tag_Name_trial641_-_sh1",
            "tag_Name_trial635_-_idx1",
            "tag_Name_trial635_-_idx3",
            "tag_Name_trial635_-_idx2",
            "tag_FQDN_idx2_trial619_splunkcloud_com",
            "tag_FQDN_idx2_k14_splunkcloud_com",
            "tag_FQDN_idx2_trial641_splunkcloud_com",
            "security_group_funtomic-prod",
            "tag_Name_trial628_-_idx2",
            "tag_FQDN_idx1_trial639_splunkcloud_com",
            "tag_Name_trial627_-_sh1",
            "tag_Name_trial645_-_sh1",
            "security_group_zabbix-server",
            "tag_Name_trial633_-_idx3",
            "tag_Name_trial633_-_idx2",
            "tag_Name_trial633_-_idx1",
            "tag_Name_finra_-_sh1",
            "tag_Name_trial630_-_idx3",
            "tag_FQDN_idx2_trial638_splunkcloud_com",
            "tag_FQDN_idx1_trial625_splunkcloud_com",
            "tag_Stack_trial637",
            "tag_FQDN_sh1_motionsoft_splunkcloud_com",
            "tag_Ticket_CO-642",
            "tag_FQDN_idx3_trial625_splunkcloud_com",
            "tag_Ticket_CO-643",
            "tag_Name_anaplan_-_idx3",
            "tag_Name_anaplan_-_idx2",
            "tag_Name_anaplan_-_idx1",
            "tag_FQDN_idx2_trial625_splunkcloud_com",
            "tag_Name_trial637_-_idx3",
            "tag_Name_trial637_-_idx2",
            "tag_Name_trial637_-_idx1",
            "tag_FQDN_idx3_mindtouch_splunkcloud_com",
            "security_group_backupify",
            "tag_Name_trial616_-_idx2",
            "tag_Name_trial616_-_idx3",
            "tag_Name_trial616_-_idx1",
            "tag_Name_white-ops_-_idx1",
            "tag_Name_white-ops_-_idx2",
            "tag_Name_white-ops_-_idx3",
            "tag_FQDN_idx1_mckesson_splunkcloud_com",
            "tag_Name_trial636_-_idx1",
            "tag_Name_trial636_-_idx2",
            "tag_Name_trial636_-_idx3",
            "tag_FQDN_sh1_trial619_splunkcloud_com",
            "tag_FQDN_sh1_mckesson_splunkcloud_com",
            "tag_FQDN_idx3_trial621_splunkcloud_com",
            "tag_FQDN_sh1_trial641_splunkcloud_com",
            "tag_Name_k14_-_sh1",
            "tag_FQDN_sh1_trial627_splunkcloud_com",
            "tag_BuildUser_Ravi_Anandwala",
            "tag_Name_trial607_-_idx1",
            "tag_Name_trial607_-_idx2",
            "tag_Name_trial607_-_idx3",
            "tag_Ticket_CO-818",
            "tag_Stack_trial639",
            "tag_Stack_trial638",
            "tag_Stack_trial635",
            "tag_Stack_trial634",
            "tag_Stack_trial636",
            "tag_Stack_trial631",
            "tag_Stack_trial630",
            "tag_Stack_trial633",
            "tag_Stack_trial632",
            "key_infra_zabbix",
            "tag_FQDN_idx1_trial613_splunkcloud_com",
            "tag_FQDN_sh1_poc1_splunkcloud_com",
            "tag_Ticket_CO-820",
            "tag_Ticket_CO-821",
            "tag_FQDN_idx2_trial628_splunkcloud_com",
            "key_infra_trial638",
            "key_infra_trial639",
            "tag_FQDN_idx2_trial632_splunkcloud_com",
            "key_infra_trial630",
            "key_infra_trial631",
            "key_infra_trial632",
            "key_infra_trial633",
            "key_infra_trial634",
            "key_infra_trial635",
            "key_infra_trial636",
            "key_infra_trial637",
            "tag_FQDN_idx3_motionsoft_splunkcloud_com",
            "tag_Stack_poc4",
            "tag_Ticket_CO-495",
            "tag_Name_gilt_-_idx1",
            "tag_FQDN_idx2_sonos_splunkcloud_com",
            "tag_FQDN_sh1_marriott_splunkcloud_com",
            "tag_Stack_poc1",
            "tag_Name_gilt_-_idx5",
            "tag_FQDN_idx2_trial616_splunkcloud_com",
            "tag_FQDN_idx1_trial627_splunkcloud_com",
            "tag_Ticket_CO-853",
            "tag_Name_anaplan_-_sh1",
            "tag_FQDN_idx1_defensenet_splunkcloud_com",
            "security_group_trial609",
            "security_group_trial605",
            "security_group_trial606",
            "tag_Name_trial611_-_sh1",
            "tag_FQDN_idx2_trial615_splunkcloud_com",
            "tag_Name_take2_-_idx3",
            "tag_Name_take2_-_idx2",
            "tag_FQDN_sh1_trial606_splunkcloud_com",
            "tag_Name_sonos_-_sh1",
            "tag_FQDN_idx3_trial623_splunkcloud_com",
            "tag_Ticket_CO-251",
            "tag_Name_idexx_-_idx1",
            "tag_FQDN_idx1_trial646_splunkcloud_com",
            "key_infra_poc5",
            "tag_Ticket_CO-822",
            "tag_FQDN_idx2_defensenet_splunkcloud_com",
            "key_infra_k14",
            "tag_FQDN_idx2_trial646_splunkcloud_com",
            "tag_Stack_climate",
            "tag_Name_motionsoft_-_sh1",
            "tag_Name_mckesson_-_sh1",
            "tag_FQDN_idx1_trial647_splunkcloud_com",
            "tag_FQDN_idx2_trial618_splunkcloud_com",
            "security_group_climate",
            "tag_Name_finra_-_idx4",
            "tag_Name_mindtouch_-_sh1",
            "tag_Name_finra_-_idx2",
            "tag_Name_finra_-_idx3",
            "tag_FQDN_idx3_trial628_splunkcloud_com",
            "tag_FQDN_idx1_poc3_splunkcloud_com",
            "tag_FQDN_idx1_poc5_splunkcloud_com",
            "tag_FQDN_idx2_trial645_splunkcloud_com",
            "tag_Name_poc1_-_idx2",
            "tag_Name_poc1_-_idx3",
            "tag_Name_backupify_-_idx2",
            "tag_Name_poc1_-_idx1",
            "tag_Name_trial614_-_idx2",
            "tag_FQDN_idx2_climate_splunkcloud_com",
            "key_infra_intermedia",
            "tag_FQDN_sh1_k14_splunkcloud_com",
            "security_group_poc4",
            "security_group_poc5",
            "tag_FQDN_idx5_finra_splunkcloud_com",
            "security_group_poc1",
            "security_group_poc2",
            "security_group_poc3",
            "tag_Name_trial626_-_idx1",
            "tag_Name_trial626_-_idx3",
            "tag_Name_trial626_-_idx2",
            "tag_FQDN_idx3_sonos_splunkcloud_com",
            "tag_FQDN_idx2_trial643_splunkcloud_com",
            "tag_Stack_gilt",
            "tag_Name_trial623_-_idx2",
            "tag_Name_trial623_-_idx3",
            "tag_Name_trial623_-_idx1",
            "tag_Name_funtomic-prod_-_sh1",
            "key_infra_whisper",
            "tag_FQDN_idx1_trial631_splunkcloud_com",
            "tag_FQDN_idx3_trial638_splunkcloud_com",
            "tag_Name_poc1_-_sh1",
            "tag_FQDN_idx2_trial630_splunkcloud_com",
            "tag_FQDN_idx1_funtomic-prod_splunkcloud_com",
            "tag_Name_prod-chef",
            "tag_FQDN_idx2_trial627_splunkcloud_com",
            "tag_Name_trial605_-_idx2",
            "tag_Name_trial605_-_idx3",
            "tag_Name_lyft_-_idx3",
            "tag_Name_trial605_-_idx1",
            "tag_Name_trial632_-_idx1",
            "tag_Name_trial632_-_idx2",
            "tag_Name_trial632_-_idx3",
            "tag_Name_trial619_-_sh1",
            "tag_FQDN_idx1_trial642_splunkcloud_com",
            "tag_Name_trial643_-_sh1",
            "tag_FQDN_idx2_lyft_splunkcloud_com",
            "tag_Name_trial639_-_sh1",
            "tag_Name_gilt_-_idx3",
            "tag_Name_marriott_-_lm1",
            "tag_FQDN_idx3_backupify_splunkcloud_com",
            "key_tower",
            "tag_Name_defensenet_-_idx3",
            "tag_Name_defensenet_-_idx1",
            "tag_FQDN_sh1_poc4_splunkcloud_com",
            "tag_Name_gilt_-_idx6",
            "tag_Stack_trial644",
            "tag_Name_trial615_-_idx2",
            "tag_Stack_trial646",
            "tag_Stack_trial647",
            "tag_Stack_trial640",
            "tag_Stack_trial641",
            "tag_Stack_trial642",
            "tag_Stack_trial643",
            "tag_FQDN_sh1_take2_splunkcloud_com",
            "tag_Name_lyft_-_idx1",
            "tag_Stack_poc3",
            "tag_Name_trial638_-_idx2",
            "tag_Name_trial638_-_idx3",
            "tag_Name_trial638_-_idx1",
            "tag_Name_sc-vpc-nat",
            "tag_Name_trial630_-_sh1",
            "tag_FQDN_idx1_trial605_splunkcloud_com",
            "tag_FQDN_sh1_trial646_splunkcloud_com",
            "tag_Stack_trial616",
            "tag_FQDN_idx2_poc2_splunkcloud_com",
            "tag_FQDN_sh1_trial639_splunkcloud_com",
            "tag_Ticket_CO-814",
            "tag_Ticket_CO-817",
            "tag_Ticket_CO-816",
            "tag_Ticket_CO-810",
            "tag_Ticket_CO-813",
            "tag_Ticket_CO-819",
            "tag_Stack_trial612",
            "tag_Stack_funtomic-prod",
            "tag_FQDN_idx3_poc2_splunkcloud_com",
            "tag_Name_trial640_-_sh1",
            "tag_FQDN_idx1_trial615_splunkcloud_com",
            "tag_Name_trial606_-_idx3",
            "tag_Name_trial606_-_idx2",
            "tag_Name_trial606_-_idx1",
            "tag_FQDN_sh1_poc3_splunkcloud_com",
            "tag_customer_type_Ops",
            "tag_Name_stackmakr-ops-blue_-_ops-blue-exec03__vpc_2_",
            "tag_FQDN_idx1_trial645_splunkcloud_com",
            "tag_FQDN_idx1_intermedia_splunkcloud_com",
            "tag_FQDN_sh1_trial628_splunkcloud_com",
            "tag_Name_trial637_-_sh1",
            "security_group_trail615",
            "tag_Ticket_CO-854",
            "tag_Ticket_CO-760",
            "tag_Name_climate_-_sh1",
            "tag_FQDN_idx3_trial618_splunkcloud_com",
            "tag_Name_sc-vpc-nat__subnet_2_",
            "tag_FQDN_idx3_take2_splunkcloud_com",
            "key_infra_mckesson",
            "tag_Name_lyft_-_sh1",
            "tag_Name_trial615_-_idx1",
            "tag_Name_funtomic-prod_-_idx3",
            "tag_Name_funtomic-prod_-_idx2",
            "tag_Name_funtomic-prod_-_idx1",
            "tag_Name_trial638_-_sh1",
            "tag_FQDN_idx1_motionsoft_splunkcloud_com",
            "tag_FQDN_idx1_gilt_splunkcloud_com",
            "tag_FQDN_idx2_poc1_splunkcloud_com",
            "tag_FQDN_idx2_trial633_splunkcloud_com",
            "tag_FQDN_idx1_trial637_splunkcloud_com",
            "tag_FQDN_idx3_idexx_splunkcloud_com",
            "tag_Name_trial615_-_sh1",
            "tag_FQDN_idx3_trial613_splunkcloud_com",
            "tag_Stack_marriott",
            "tag_Stack_k14",
            "tag_Ticket_CO-739",
            "tag_Name_motionsoft_-_idx3",
            "tag_FQDN_idx1_trial618_splunkcloud_com",
            "tag_FQDN_idx3_trial629_splunkcloud_com",
            "tag_FQDN_idx1_k14_splunkcloud_com",
            "tag_FQDN_sh1_trial616_splunkcloud_com",
            "tag_Name_tower",
            "tag_FQDN_idx2_trial607_splunkcloud_com",
            "tag_Name_trial622_-_idx3",
            "tag_Stack_trial606",
            "tag_Stack_trial607",
            "tag_Stack_trial609",
            "tag_Name_take2_-_idx1",
            "tag_Name_trial621_-_idx1",
            "tag_FQDN_idx3_trial631_splunkcloud_com",
            "tag_FQDN_lm1_poc5_splunkcloud_com",
            "tag_Stack_take2",
            "tag_FQDN_zabbix1_zabbix_splunkcloud_com",
            "tag_Name_trial621_-_idx3",
            "tag_Name_finra_-_idx5",
            "tag_FQDN_idx3_trial641_splunkcloud_com",
            "tag_Stack_trial625",
            "tag_FQDN_idx1_trial643_splunkcloud_com",
            "tag_Name_trial628_-_idx3",
            "tag_FQDN_idx3_trial637_splunkcloud_com",
            "tag_whisper_version_SEC-1318-20130212T1441-WR_16_HF2",
            "security_group_lyft",
            "tag_Stack_trial620",
            "tag_Name_trial629_-_idx3",
            "tag_Name_poc2_-_idx3",
            "tag_Name_poc2_-_idx2",
            "type_c3_8xlarge",
            "tag_Ticket_CO-865",
            "tag_Name_trial625_-_idx1",
            "tag_Name_trial625_-_idx2",
            "tag_FQDN_idx3_trial640_splunkcloud_com",
            "tag_FQDN_sh1_trial609_splunkcloud_com",
            "tag_FQDN_idx3_trial644_splunkcloud_com",
            "tag_FQDN_sh1_anaplan_splunkcloud_com",
            "tag_Stack_lyft",
            "tag_FQDN_idx1_trial632_splunkcloud_com",
            "tag_Name_trial611_-_idx3",
            "tag_Ticket_CO-815",
            "tag_Name_intermedia_-_idx3",
            "tag_FQDN_sh1_intermedia_splunkcloud_com",
            "tag_FQDN_idx1_trial635_splunkcloud_com",
            "tag_FQDN_idx3_defensenet_splunkcloud_com",
            "security_group_cluster-master",
            "tag_FQDN_sh1_trial629_splunkcloud_com",
            "key_infra_trial629",
            "tag_FQDN_idx2_trial621_splunkcloud_com",
            "key_infra_trial627",
            "key_infra_trial625",
            "key_infra_trial623",
            "key_infra_trial622",
            "tag_FQDN_sh1_gilt_splunkcloud_com",
            "key_infra_trial620",
            "tag_FQDN_idx2_trial622_splunkcloud_com",
            "tag_FQDN_idx2_trial609_splunkcloud_com",
            "tag_Name_mindtouch_-_idx3",
            "tag_FQDN_idx2_gilt_splunkcloud_com",
            "tag_FQDN_idx1_trial616_splunkcloud_com",
            "tag_FQDN_idx1_trial629_splunkcloud_com",
            "tag_FQDN_sh1_trial633_splunkcloud_com",
            "tag_FQDN_idx1_trial614_splunkcloud_com",
            "security_group_license-master",
            "tag_whisper_version____SEC-1639-20140414T1539-WR_17_HF3",
            "tag_Name_intermedia_-_idx9",
            "tag_Name_finra_-_idx1",
            "tag_Name_trial625_-_sh1",
            "tag_FQDN_idx3_trial611_splunkcloud_com",
            "tag_FQDN_idx2_marriott_splunkcloud_com",
            "tag_Role_zabbix-server",
            "tag_Name_marriott_-_idx1",
            "tag_FQDN_idx3_intermedia_splunkcloud_com",
            "tag_Name_marriott_-_idx3",
            "tag_Name_marriott_-_idx2",
            "tag_Name_poc5_-_lm1",
            "tag_Name_trial620_-_sh1",
            "security_group_finra_sh",
            "tag_FQDN_sh1_lyft_splunkcloud_com",
            "tag_Name_trial617_-_idx1",
            "tag_FQDN_idx2_trial640_splunkcloud_com",
            "tag_Name_trial617_-_idx3",
            "tag_Name_trial617_-_idx2",
            "tag_Name_trial629_-_sh1",
            "tag_FQDN_sh1_trial637_splunkcloud_com",
            "tag_FQDN_sh1_mindtouch_splunkcloud_com",
            "tag_Name_trial644_-_sh1",
            "tag_Ticket_CO-652",
            "tag_Stack_anaplan",
            "type_m1_small",
            "tag_Name_trial640_-_idx2",
            "tag_Ticket_CO-436",
            "tag_Name_take2_-_sh1",
            "tag_FQDN_idx5_intermedia_splunkcloud_com",
            "tag_Name_trial626_-_sh1",
            "tag_Ticket_CO-182",
            "security_group_splunk_wideopen",
            "tag_FQDN_idx3_climate_splunkcloud_com",
            "tag_Ticket_CO-682",
            "tag_Name_motionsoft_-_idx2",
            "security_group_mckesson",
            "tag_Name_motionsoft_-_idx1",
            "tag_Name_trial619_-_idx2",
            "tag_Ticket_CO-758",
            "tag_Ticket_CO-759",
            "tag_Ticket_CO-756",
            "tag_Ticket_CO-757",
            "tag_Ticket_CO-754",
            "tag_Ticket_CO-755",
            "tag_Ticket_CO-752",
            "tag_Ticket_CO-753",
            "tag_Ticket_CO-750",
            "tag_Ticket_CO-751",
            "security_group_anaplan_",
            "tag_Name_mindtouch_-_idx2",
            "tag_Name_mindtouch_-_idx1",
            "tag_FQDN_sh1_trial630_splunkcloud_com",
            "tag_BuildUser_Chris_Boniak",
            "tag_FQDN_idx2_spm1_splunkcloud_com",
            "tag_Ticket_CO-639",
            "tag_Name_poc5_-_c0m1",
            "tag_FQDN_sh1_trial621_splunkcloud_com",
            "tag_Name_trial605_-_sh1",
            "tag_Name_trial621_-_sh1",
            "tag_FQDN_idx3_trial617_splunkcloud_com"
        ],
        "hosts": [
            "54.86.87.25",
            "54.86.99.25",
            "54.84.251.0",
            "54.86.98.158",
            "54.209.76.22",
            "54.84.180.204",
            "54.86.40.17",
            "54.84.191.190",
            "54.84.23.79",
            "54.86.102.132",
            "54.84.222.25",
            "54.84.207.241",
            "54.85.157.183",
            "54.86.112.106",
            "54.86.65.171",
            "54.86.90.177",
            "54.86.110.115",
            "54.84.114.2",
            "54.85.71.54",
            "54.86.78.51",
            "54.86.39.175",
            "54.85.249.26",
            "54.86.56.174",
            "54.86.98.67",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "54.86.10.255",
            "54.86.101.162",
            "54.86.87.183",
            "54.85.146.9",
            "54.86.81.213",
            "54.84.74.125",
            "54.85.193.109",
            "54.85.48.70",
            "54.208.141.20",
            "54.84.156.145",
            "54.85.223.164",
            "54.84.164.99",
            "54.84.125.108",
            "54.86.106.244",
            "54.86.82.149",
            "54.84.103.231",
            "54.85.173.90",
            "54.86.96.151",
            "54.84.65.195",
            "54.86.80.199",
            "54.209.162.114",
            "54.85.75.4",
            "54.84.190.144",
            "54.86.111.203",
            "54.86.94.75",
            "54.86.94.149",
            "54.86.23.145",
            "54.86.74.37",
            "54.85.27.197",
            "54.85.28.140",
            "54.86.112.135",
            "54.85.181.37",
            "54.85.33.186",
            "54.85.91.87",
            "54.84.222.7",
            "54.85.21.183",
            "54.86.98.77",
            "54.85.47.154",
            "54.86.125.136",
            "54.86.14.157",
            "54.86.99.249",
            "54.208.59.237",
            "54.86.81.225",
            "54.86.117.162",
            "54.86.103.5",
            "54.209.127.172",
            "54.86.117.161",
            "54.209.74.106",
            "54.86.108.101",
            "54.84.75.99",
            "54.85.193.223",
            "54.84.116.38",
            "54.85.248.82",
            "54.85.161.87",
            "54.86.116.105",
            "54.85.160.181",
            "54.86.77.91",
            "54.86.64.168",
            "54.85.54.254",
            "54.85.199.140",
            "54.86.90.152",
            "54.84.81.3",
            "54.209.177.56",
            "54.84.99.227",
            "54.85.126.177",
            "54.84.37.150",
            "54.85.42.39",
            "54.85.48.128",
            "54.84.155.209",
            "54.84.103.10",
            "54.86.75.36",
            "54.85.77.167",
            "54.84.164.51",
            "54.86.112.102",
            "54.209.120.55",
            "54.84.0.249",
            "54.85.90.7",
            "54.86.109.129",
            "54.86.141.187",
            "54.84.167.146",
            "54.85.69.157",
            "54.86.109.121",
            "54.86.111.175",
            "54.86.117.163",
            "54.85.166.231",
            "54.84.47.238",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "54.85.72.146",
            "54.86.93.172",
            "54.208.12.112",
            "54.208.210.176",
            "54.84.15.178",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "54.86.76.239",
            "54.86.108.117",
            "54.85.102.208",
            "54.209.108.176",
            "54.86.98.21",
            "54.86.97.227",
            "54.85.76.42",
            "54.208.124.14",
            "54.86.108.119",
            "54.209.183.210",
            "54.85.167.62",
            "54.86.54.174",
            "54.84.174.209",
            "54.85.119.67",
            "54.85.10.98",
            "54.85.80.156",
            "54.85.14.238",
            "54.209.108.61",
            "54.85.53.103",
            "54.208.45.55",
            "54.85.32.12",
            "54.208.89.118",
            "54.84.199.223",
            "54.84.166.253",
            "54.85.53.185",
            "54.85.34.98",
            "54.86.57.201",
            "54.86.117.237",
            "54.85.68.39",
            "54.208.96.71",
            "54.85.149.164",
            "54.86.53.153",
            "54.86.84.127",
            "54.84.152.213",
            "54.86.90.15",
            "54.85.208.32",
            "54.85.255.219",
            "54.86.84.64",
            "54.84.148.213",
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "54.84.80.225",
            "54.84.240.188",
            "54.86.108.102",
            "54.86.107.51",
            "54.85.148.231",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "54.209.139.239",
            "54.86.53.77",
            "54.85.71.17",
            "54.86.141.183",
            "54.86.97.99",
            "54.86.141.184",
            "54.86.92.153",
            "54.209.14.115",
            "54.86.100.62",
            "54.84.189.79",
            "54.86.3.216",
            "54.86.119.45",
            "54.86.71.155",
            "54.86.90.142",
            "54.85.80.174",
            "54.208.228.127",
            "54.84.41.152",
            "54.84.252.121",
            "54.84.87.73",
            "54.85.175.102",
            "54.85.37.235",
            "54.84.92.185",
            "54.85.127.222",
            "54.86.97.181",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "54.86.103.185",
            "54.84.54.49",
            "54.85.44.185",
            "54.208.10.193",
            "54.86.116.199",
            "54.86.106.241",
            "54.86.106.243",
            "54.86.106.242",
            "ec2-23-20-41-80.compute-1.amazonaws.com",
            "54.86.89.186",
            "54.85.148.101",
            "54.86.105.40",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "54.85.47.190",
            "54.84.142.102",
            "54.84.97.29",
            "54.86.50.215",
            "54.86.90.204",
            "54.86.88.52",
            "54.84.190.109",
            "54.86.78.119",
            "54.84.241.208",
            "ec2-54-242-229-223.compute-1.amazonaws.com",
            "54.86.79.232",
            "54.86.104.169",
            "54.86.67.89",
            "54.84.137.179",
            "54.85.42.61",
            "54.86.81.21",
            "54.86.104.18",
            "54.84.199.152",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "54.85.66.59",
            "54.84.122.210",
            "54.86.80.36",
            "54.85.135.14",
            "54.85.98.144",
            "54.209.106.125",
            "54.86.76.41",
            "54.84.31.76",
            "54.86.80.182",
            "54.86.88.208",
            "54.84.217.136",
            "54.86.94.238",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-50-19-44-148.compute-1.amazonaws.com",
            "54.86.38.49",
            "54.84.242.116",
            "54.85.13.176",
            "54.85.11.117",
            "54.86.48.214",
            "54.85.200.49",
            "54.85.65.51",
            "54.86.81.117",
            "54.85.52.64",
            "54.86.111.80",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "54.85.69.123",
            "54.84.206.192",
            "ec2-54-80-236-42.compute-1.amazonaws.com",
            "54.86.8.229",
            "54.85.75.200",
            "54.84.84.233",
            "54.86.75.79",
            "54.209.203.222",
            "54.85.85.59",
            "54.86.97.174",
            "54.86.80.208",
            "54.84.193.141",
            "54.84.169.33",
            "54.84.42.12",
            "54.86.97.73",
            "54.84.156.195",
            "54.86.91.120",
            "54.85.170.154",
            "54.85.45.216",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "54.84.228.141",
            "54.84.149.162",
            "54.85.207.233",
            "54.86.85.22",
            "54.85.61.212",
            "54.86.61.31",
            "54.86.101.141",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "54.86.80.163",
            "54.208.187.98",
            "54.84.84.30",
            "54.84.46.105",
            "54.86.52.195",
            "54.84.189.117",
            "54.86.94.44",
            "54.86.128.114",
            "54.84.21.94",
            "54.86.90.71",
            "54.209.204.12",
            "54.86.111.172",
            "54.86.55.72",
            "54.84.192.78",
            "54.86.110.180",
            "54.84.149.25",
            "54.85.95.0",
            "54.86.45.250",
            "54.84.189.190",
            "54.86.60.192",
            "54.85.87.129",
            "54.84.245.162",
            "54.86.97.144",
            "54.84.170.133",
            "54.86.97.67",
            "54.86.99.19",
            "54.86.51.77",
            "54.208.87.90",
            "54.85.84.167",
            "54.84.185.247",
            "54.84.245.20",
            "54.85.196.193",
            "54.86.89.139",
            "54.86.60.175",
            "54.85.251.175",
            "54.86.85.33",
            "54.84.18.13",
            "54.86.112.246",
            "54.85.52.37",
            "54.86.112.96",
            "54.85.16.252",
            "54.86.117.236",
            "54.84.163.82",
            "10.219.92.64",
            "10.219.53.81",
            "10.219.102.143",
            "10.219.79.196",
            "10.219.36.226",
            "10.219.53.83",
            "10.219.27.228",
            "10.219.55.210",
            "10.219.142.223",
            "10.219.81.15",
            "10.219.174.165",
            "10.219.62.184",
            "10.219.62.182",
            "10.219.105.247",
            "10.219.165.247",
            "10.219.63.67",
            "10.219.166.184",
            "10.219.53.235",
            "10.219.70.210",
            "10.219.1.1",
            "10.219.114.130",
            "10.219.89.30",
            "10.219.84.189",
            "10.219.177.177",
            "10.219.131.132",
            "10.219.103.26",
            "10.219.131.134",
            "10.219.165.236",
            "10.219.9.24",
            "10.219.173.45",
            "10.219.185.101",
            "10.219.100.237",
            "10.219.169.135",
            "10.219.112.253",
            "10.219.13.250",
            "10.219.132.135",
            "10.219.183.41",
            "10.219.161.181",
            "10.219.175.162",
            "10.219.144.224",
            "10.219.135.107",
            "10.219.18.251",
            "10.219.25.26",
            "10.219.68.240",
            "10.219.60.118",
            "10.219.49.54",
            "10.219.78.180",
            "10.219.62.128",
            "10.219.77.162",
            "10.219.185.140",
            "10.219.10.200",
            "10.219.12.148",
            "10.219.59.159",
            "10.219.12.146",
            "10.219.41.127",
            "10.219.158.35",
            "10.219.43.48",
            "10.219.5.238",
            "10.219.154.94",
            "10.219.130.229",
            "10.219.161.92",
            "10.219.43.249",
            "10.219.107.166",
            "10.219.163.151",
            "10.219.121.158",
            "10.219.1.219",
            "10.219.164.210",
            "10.219.57.225",
            "10.219.28.211",
            "10.219.1.9",
            "10.219.64.58",
            "10.219.81.29",
            "10.219.152.17",
            "10.219.138.185",
            "10.219.78.69",
            "10.219.137.49",
            "10.219.18.12",
            "10.219.136.66",
            "10.219.48.23",
            "10.219.41.230",
            "10.219.41.239",
            "10.219.98.192",
            "10.219.56.91",
            "10.219.143.130",
            "10.219.180.178",
            "10.219.12.138",
            "10.219.115.77",
            "10.219.40.153",
            "10.219.177.41",
            "10.219.168.41",
            "10.219.75.209",
            "10.219.140.250",
            "10.219.36.162",
            "10.219.92.102",
            "10.219.167.0",
            "10.219.169.68",
            "10.219.110.47",
            "10.219.91.14",
            "10.219.88.75",
            "10.219.71.223",
            "10.219.175.97",
            "10.219.14.143",
            "10.219.54.28",
            "10.219.122.228",
            "10.219.49.11",
            "10.219.131.26",
            "10.219.113.16",
            "10.219.146.30",
            "10.219.41.51",
            "10.219.154.211",
            "10.219.19.226",
            "10.219.153.9",
            "10.219.57.108",
            "10.219.11.33",
            "10.219.169.253",
            "10.219.142.152",
            "10.219.3.22",
            "10.219.189.153",
            "10.219.24.179",
            "10.219.25.150",
            "10.219.152.253",
            "10.219.187.219",
            "10.219.36.235",
            "10.219.117.252",
            "10.219.51.0",
            "10.219.62.192",
            "10.219.39.9",
            "10.219.191.53",
            "10.219.101.155",
            "10.219.93.172",
            "10.219.183.156",
            "10.219.26.152",
            "10.219.169.240",
            "10.219.64.217",
            "10.219.38.61",
            "10.219.160.142",
            "10.219.183.205",
            "10.219.134.206",
            "10.219.155.123",
            "10.219.86.47",
            "10.219.37.213",
            "10.219.107.232",
            "10.219.82.113",
            "10.219.142.242",
            "10.219.17.208",
            "10.219.40.115",
            "10.219.30.68",
            "10.219.145.78",
            "10.219.64.87",
            "10.219.64.89",
            "10.219.137.205",
            "10.219.126.78",
            "10.219.47.1",
            "10.219.118.63",
            "10.219.45.70",
            "10.219.92.107",
            "10.219.85.31",
            "10.219.85.37",
            "10.219.9.203",
            "10.219.181.82",
            "10.219.125.7",
            "10.219.101.208",
            "10.219.28.78",
            "10.219.75.150",
            "10.219.26.28",
            "10.219.72.12",
            "10.219.123.229",
            "10.219.20.163",
            "10.219.114.210",
            "10.219.26.182",
            "10.219.10.83",
            "10.219.43.2",
            "10.219.119.27",
            "10.219.173.21",
            "10.219.103.178",
            "10.219.11.70",
            "10.219.117.146",
            "10.219.137.105",
            "10.219.156.153",
            "10.219.8.78",
            "10.219.68.254",
            "10.219.81.130",
            "10.219.67.120",
            "10.219.83.87",
            "10.219.4.55",
            "10.219.96.145",
            "10.219.72.93",
            "10.219.61.3",
            "10.219.147.74",
            "10.219.118.126",
            "10.219.25.43",
            "10.219.69.7",
            "10.219.31.47",
            "10.219.163.166",
            "10.219.136.200",
            "10.219.56.242",
            "10.219.0.222",
            "10.219.150.186",
            "10.219.129.226",
            "10.219.91.109",
            "10.219.65.35",
            "10.219.63.147",
            "10.219.155.112",
            "10.219.128.183",
            "10.219.49.157",
            "10.219.97.207",
            "10.219.90.205",
            "10.219.5.111",
            "10.219.109.144",
            "10.219.180.244",
            "10.219.177.150",
            "10.219.22.111",
            "10.219.50.231",
            "10.219.90.31",
            "10.219.190.234",
            "10.219.184.95",
            "10.219.87.56",
            "10.219.56.44",
            "10.219.39.139",
            "10.219.151.162",
            "10.219.154.115",
            "10.219.36.26",
            "10.219.85.43",
            "10.219.152.142",
            "10.219.94.27",
            "10.219.155.180",
            "10.219.107.101",
            "10.219.42.72",
            "10.219.16.100",
            "10.219.186.145",
            "10.219.167.28",
            "10.219.16.66",
            "10.219.179.164",
            "10.219.188.5",
            "10.219.41.191",
            "10.219.136.115",
            "10.219.41.67",
            "10.219.130.190",
            "10.219.154.203",
            "10.219.119.78",
            "10.219.164.166",
            "10.219.177.243",
            "10.219.168.89",
            "10.219.177.248",
            "10.219.119.218",
            "10.219.15.194",
            "10.219.137.67",
            "10.219.154.12",
            "10.219.145.106",
            "10.219.157.181",
            "10.219.128.227",
            "10.219.159.21",
            "10.219.35.86",
            "10.219.3.208",
            "10.219.26.121",
            "10.219.16.214",
            "10.219.100.34",
            "10.219.64.207",
            "10.219.103.216",
            "10.219.50.248",
            "10.219.133.48",
            "10.219.43.57",
            "10.219.97.127",
            "10.219.97.123",
            "10.219.18.88",
            "10.219.18.78",
            "10.219.143.239",
            "10.219.120.23",
            "10.219.165.216",
            "10.219.140.138",
            "10.219.118.52",
            "10.219.11.190",
            "10.219.4.113",
            "10.219.74.178",
            "10.219.9.213",
            "10.219.2.93",
            "10.219.79.157",
            "10.219.14.89",
            "10.219.31.244",
            "10.219.5.147",
            "10.219.136.17",
            "10.219.59.221",
            "10.219.136.13",
            "10.219.4.181",
            "10.219.86.78",
            "10.219.63.105",
            "10.219.153.220",
            "10.219.114.207",
            "10.219.146.42",
            "10.219.2.72",
            "10.219.173.37",
            "10.219.16.89",
            "10.219.173.38",
            "10.219.49.237",
            "10.219.48.166",
            "10.219.112.202",
            "10.219.27.75",
            "10.219.175.103",
            "10.219.179.119",
            "10.219.142.23",
            "10.219.68.180",
            "10.219.109.92",
            "10.219.77.13",
            "10.219.154.235",
            "10.219.85.120",
            "10.219.147.63",
            "10.219.11.12",
            "10.219.130.240",
            "10.219.47.118",
            "10.219.47.252",
            "10.219.166.38",
            "10.219.18.43",
            "10.219.97.164",
            "10.219.121.80",
            "10.219.130.129",
            "10.219.124.145",
            "10.219.68.99",
            "10.219.72.134",
            "10.219.93.219",
            "10.219.123.163",
            "10.219.111.113",
            "10.219.165.155",
            "10.219.78.42",
            "10.219.155.57",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.133.98",
            "10.219.184.234",
            "10.219.81.201",
            "10.219.142.198",
            "10.219.98.174",
            "10.219.98.173",
            "10.219.61.154",
            "10.219.89.22",
            "10.219.185.71",
            "10.219.185.186",
            "10.219.60.213",
            "10.219.127.143",
            "10.219.128.18",
            "10.219.95.221",
            "10.219.156.2",
            "10.219.171.92",
            "10.219.91.234",
            "10.219.108.141",
            "10.219.33.86",
            "10.219.71.164",
            "10.219.182.240",
            "10.219.48.124",
            "10.219.90.109",
            "10.219.29.108",
            "10.219.186.171",
            "10.219.84.105",
            "10.219.115.245",
            "10.219.43.120",
            "10.219.39.194",
            "10.219.63.214",
            "10.219.132.7",
            "10.219.147.27",
            "10.219.132.1",
            "10.219.147.25",
            "10.219.67.44",
            "10.219.158.176",
            "10.219.52.205",
            "10.219.59.57",
            "10.219.130.1",
            "10.219.168.254",
            "10.219.109.28",
            "10.219.20.248",
            "10.219.142.79",
            "10.219.187.178",
            "10.219.127.168",
            "10.219.127.169",
            "10.219.16.141",
            "10.219.2.224",
            "10.219.30.9",
            "10.219.129.154",
            "10.219.137.198",
            "10.219.118.148",
            "10.219.179.156",
            "10.219.189.219",
            "10.219.138.5",
            "10.219.149.40",
            "10.219.119.127",
            "10.219.6.165",
            "10.219.68.40",
            "10.219.68.47",
            "10.217.79.144",
            "10.219.138.98",
            "10.219.9.54",
            "10.219.143.228",
            "10.219.150.33",
            "10.219.89.90",
            "10.219.132.76",
            "10.219.75.107",
            "10.219.49.160",
            "10.219.94.77",
            "10.219.134.176",
            "10.219.12.85",
            "10.219.115.61",
            "10.219.134.179",
            "10.219.92.4",
            "10.219.37.47",
            "10.219.56.83",
            "10.219.147.195",
            "10.219.5.136",
            "10.219.36.177",
            "10.219.103.150",
            "10.219.100.175",
            "10.219.66.5",
            "10.219.182.219",
            "10.219.78.250",
            "10.219.184.152",
            "10.219.66.9",
            "10.219.92.169",
            "10.219.125.232",
            "10.219.67.205",
            "10.219.32.233",
            "10.219.32.235",
            "10.219.111.126",
            "10.219.36.102",
            "10.219.39.144",
            "10.219.32.78",
            "10.219.56.12",
            "10.219.162.164",
            "10.219.4.79",
            "10.219.178.84",
            "10.219.178.85",
            "10.219.150.111",
            "10.219.51.115",
            "10.219.47.66",
            "10.219.32.15",
            "10.219.23.181",
            "10.219.154.60",
            "10.219.173.93",
            "10.219.154.184",
            "10.219.60.102",
            "10.219.73.211",
            "10.219.85.245",
            "10.219.52.143",
            "10.219.17.109",
            "10.219.141.55",
            "10.219.127.193",
            "10.219.24.227",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.134.89",
            "10.219.87.108",
            "10.219.114.174",
            "10.219.10.116",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.29.254",
            "10.219.45.160",
            "10.219.147.76",
            "10.219.80.212",
            "10.219.161.188",
            "10.219.25.147",
            "10.219.164.5",
            "10.219.148.67",
            "10.219.188.151",
            "10.219.91.91",
            "10.219.111.100",
            "10.219.2.175",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.120.83",
            "10.219.111.13",
            "10.219.58.233",
            "10.219.114.9",
            "10.219.174.231",
            "10.219.167.181",
            "10.219.166.102"
        ],
        "vars": {
            "vpc_destination_variable": "private_ip_address"
        }
    },
    "_meta": {
        "hostvars": {}  # pruned to reduce the size of the dataset
    },
    "ec2": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com",
            "ec2-50-19-44-148.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.84.41.152",
            "54.84.65.195",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.28.140",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.37.150",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.189.190",
            "54.84.122.210",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.75.99",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.86.101.162",
            "54.208.124.14",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "54.208.96.71",
            "54.84.92.185",
            "54.84.42.12",
            "54.84.148.213",
            "54.84.149.25",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.86.23.145",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.217.79.144",
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.123.163",
            "10.219.92.102",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.119.218",
            "10.219.92.169",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.115.77",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.107.101",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.112.202",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.118.52",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.164.166",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.131.132",
            "10.219.160.142",
            "10.219.179.119",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.136.115",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.132.135",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.164.210",
            "10.219.161.181",
            "10.219.144.224",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.129.226",
            "10.219.142.198",
            "10.219.152.142",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.23.181",
            "10.219.14.89",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.61.154",
            "10.219.43.120",
            "10.219.26.182",
            "10.219.33.86",
            "10.219.57.225",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.50.248",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.26.121",
            "10.219.59.57",
            "10.219.41.51",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.12.148",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.25.147",
            "10.219.29.254",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "key_infra_CO-920": {
        "children": [],
        "hosts": [
            "10.219.62.215",
            "10.219.45.160",
            "10.219.10.116",
            "10.219.164.5",
            "10.219.147.76",
            "10.219.87.108"
        ],
        "vars": {}
    },
    "key_infra_anaplan": {
        "children": [],
        "hosts": [
            "10.219.1.219",
            "10.219.49.160",
            "10.219.184.95",
            "10.219.92.107",
            "10.219.117.146",
            "10.219.70.210",
            "54.86.107.51",
            "54.86.125.136",
            "54.86.94.44",
            "54.86.128.114"
        ],
        "vars": {}
    },
    "key_infra_backupify": {
        "children": [],
        "hosts": [
            "10.219.5.111",
            "10.219.63.105",
            "10.219.137.105",
            "10.219.168.41",
            "10.219.131.132",
            "10.219.91.234",
            "54.85.54.254",
            "54.85.181.37",
            "54.85.76.42",
            "54.85.68.39"
        ],
        "vars": {}
    },
    "key_infra_climate": {
        "children": [],
        "hosts": [
            "10.219.1.9",
            "10.219.4.181",
            "10.219.147.195",
            "10.219.132.7",
            "10.219.171.92",
            "10.219.68.99",
            "54.84.99.227",
            "54.84.164.51",
            "54.84.155.209",
            "54.84.142.102"
        ],
        "vars": {}
    },
    "key_infra_defensenet": {
        "children": [],
        "hosts": [
            "10.219.18.251",
            "10.219.183.156",
            "10.219.174.165",
            "10.219.154.184",
            "10.219.84.105",
            "10.219.107.166",
            "54.84.217.136",
            "54.84.116.38",
            "54.84.97.29",
            "54.85.42.39"
        ],
        "vars": {}
    },
    "key_infra_finra": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "10.219.36.226",
            "10.219.52.143",
            "10.219.62.184",
            "10.219.173.93",
            "10.219.145.78",
            "10.219.98.174",
            "10.219.127.143",
            "10.219.68.240",
            "54.84.152.213",
            "54.84.103.231",
            "54.84.156.145",
            "54.84.180.204",
            "54.84.122.210",
            "54.84.189.190",
            "54.84.80.225",
            "54.84.189.117"
        ],
        "vars": {}
    },
    "key_infra_funtomic-prod": {
        "children": [],
        "hosts": [
            "10.219.28.78",
            "10.219.190.234",
            "10.219.186.145",
            "10.219.168.89",
            "10.219.127.193",
            "10.219.113.16",
            "54.85.13.176",
            "54.84.137.179",
            "54.84.242.116",
            "54.84.222.25"
        ],
        "vars": {}
    },
    "key_infra_gilt": {
        "children": [],
        "hosts": [
            "10.219.8.78",
            "10.219.59.221",
            "10.219.38.61",
            "10.219.62.128",
            "10.219.167.28",
            "10.219.165.216",
            "10.219.156.153",
            "10.219.67.44",
            "10.219.82.113",
            "54.209.162.114",
            "54.209.183.210",
            "54.85.80.156",
            "54.84.31.76",
            "54.85.52.37",
            "54.85.47.190",
            "54.209.177.56"
        ],
        "vars": {}
    },
    "key_infra_idexx": {
        "children": [],
        "hosts": [
            "10.219.60.213",
            "10.219.153.220",
            "10.219.154.94",
            "10.219.130.229",
            "10.219.72.134",
            "10.219.94.77",
            "54.84.46.105",
            "54.85.91.87",
            "54.84.190.109",
            "54.85.148.101"
        ],
        "vars": {}
    },
    "key_infra_intermedia": {
        "children": [],
        "hosts": [
            "10.219.17.109",
            "10.219.51.115",
            "10.219.55.210",
            "10.219.41.127",
            "10.219.4.113",
            "10.219.189.219",
            "10.219.152.17",
            "10.219.169.240",
            "10.219.112.253",
            "10.219.64.207",
            "10.219.97.164",
            "10.219.118.126",
            "54.86.85.22",
            "54.84.193.141",
            "54.84.18.13",
            "54.85.193.109",
            "54.86.84.64",
            "54.85.167.62",
            "54.85.126.177",
            "54.86.75.79",
            "54.86.14.157",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "key_infra_k14": {
        "children": [],
        "hosts": [
            "10.219.35.86",
            "10.219.9.213",
            "10.219.141.55",
            "10.219.134.179",
            "10.219.155.57",
            "10.219.83.87",
            "54.84.156.195",
            "54.86.54.174",
            "54.85.37.235",
            "54.85.175.102"
        ],
        "vars": {}
    },
    "key_infra_lyft": {
        "children": [],
        "hosts": [
            "10.219.29.108",
            "10.219.3.208",
            "10.219.56.12",
            "10.219.184.152",
            "10.219.93.172",
            "10.219.103.216",
            "54.85.42.61",
            "54.208.87.90",
            "54.85.102.208",
            "54.209.139.239"
        ],
        "vars": {}
    },
    "key_infra_marriott": {
        "children": [],
        "hosts": [
            "10.219.11.12",
            "10.219.136.66",
            "10.219.136.17",
            "10.219.179.164",
            "10.219.98.192",
            "10.219.105.247",
            "54.84.125.108",
            "54.84.199.223",
            "54.84.164.99",
            "54.84.222.7",
            "54.84.206.192",
            "54.84.185.247"
        ],
        "vars": {}
    },
    "key_infra_mckesson": {
        "children": [],
        "hosts": [
            "10.219.43.48",
            "10.219.132.76",
            "10.219.147.27",
            "10.219.95.221",
            "10.219.64.89",
            "10.219.85.120",
            "54.86.141.183",
            "54.86.141.184",
            "54.86.141.187",
            "54.86.103.185"
        ],
        "vars": {}
    },
    "key_infra_mindtouch": {
        "children": [],
        "hosts": [
            "10.219.51.0",
            "10.219.152.142",
            "10.219.165.236",
            "10.219.136.115",
            "10.219.72.12",
            "10.219.69.7",
            "10.219.101.208",
            "54.86.119.45",
            "54.86.109.129",
            "54.86.109.121",
            "54.86.112.246"
        ],
        "vars": {}
    },
    "key_infra_motionsoft": {
        "children": [],
        "hosts": [
            "10.219.40.115",
            "10.219.49.237",
            "10.219.188.5",
            "10.219.112.202",
            "10.219.103.26",
            "10.219.81.130",
            "54.85.10.98",
            "54.85.16.252",
            "54.84.228.141",
            "54.85.65.51"
        ],
        "vars": {}
    },
    "key_infra_mregan": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "key_infra_poc1": {
        "children": [],
        "hosts": [
            "10.219.16.141",
            "10.219.25.43",
            "10.219.189.153",
            "10.219.182.240",
            "10.219.181.82",
            "10.219.81.15",
            "54.85.33.186",
            "54.85.66.59",
            "54.85.52.64",
            "54.85.21.183"
        ],
        "vars": {}
    },
    "key_infra_poc2": {
        "children": [],
        "hosts": [
            "10.219.32.233",
            "10.219.131.134",
            "10.219.146.30",
            "10.219.118.63",
            "10.219.85.37",
            "10.219.100.34",
            "54.85.53.103",
            "54.85.32.12",
            "54.85.28.140",
            "54.84.252.121"
        ],
        "vars": {}
    },
    "key_infra_poc3": {
        "children": [],
        "hosts": [
            "10.219.48.166",
            "10.219.49.54",
            "10.219.166.184",
            "10.219.85.245",
            "10.219.107.232",
            "10.219.126.78",
            "54.84.84.30",
            "54.85.71.17",
            "54.84.166.253",
            "54.85.71.54"
        ],
        "vars": {}
    },
    "key_infra_poc4": {
        "children": [],
        "hosts": [
            "10.219.43.57",
            "10.219.12.85",
            "10.219.137.198",
            "10.219.150.111",
            "10.219.177.243",
            "10.219.72.93",
            "54.85.69.157",
            "54.85.69.123",
            "54.85.45.216",
            "54.84.170.133"
        ],
        "vars": {}
    },
    "key_infra_poc5": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "10.219.63.147",
            "10.219.130.240",
            "10.219.169.253",
            "10.219.130.190",
            "10.219.125.232",
            "54.84.23.79",
            "54.85.80.174",
            "54.86.39.175",
            "54.85.72.146",
            "54.84.47.238",
            "54.84.74.125"
        ],
        "vars": {}
    },
    "key_infra_prod-monitor-red": {
        "children": [],
        "hosts": [
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.120.23",
            "10.219.118.52",
            "10.219.177.150",
            "10.219.144.224",
            "10.219.142.198",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.16.214",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "key_infra_sc_nat": {
        "children": [],
        "hosts": [
            "10.219.23.181",
            "10.219.164.166",
            "10.219.123.163",
            "54.208.124.14",
            "54.84.37.150",
            "54.84.41.152"
        ],
        "vars": {}
    },
    "key_infra_skynet": {
        "children": [],
        "hosts": [
            "10.219.2.93",
            "10.219.0.222",
            "10.219.12.148",
            "10.219.1.1",
            "10.219.173.21",
            "10.219.132.135",
            "10.219.186.171",
            "10.219.103.178",
            "10.219.115.77",
            "10.219.90.109",
            "10.219.92.169",
            "54.86.23.145",
            "54.85.146.9",
            "54.84.75.99",
            "54.84.189.79",
            "54.86.51.77",
            "54.85.157.183"
        ],
        "vars": {}
    },
    "key_infra_sonos": {
        "children": [],
        "hosts": [
            "10.219.56.91",
            "10.219.56.44",
            "10.219.36.235",
            "10.219.39.194",
            "10.219.154.60",
            "10.219.175.103",
            "10.219.150.186",
            "10.219.84.189",
            "10.219.71.223",
            "54.86.48.214",
            "54.86.80.199",
            "54.86.10.255",
            "54.86.56.174",
            "54.86.89.139",
            "54.86.81.117",
            "54.86.88.208"
        ],
        "vars": {}
    },
    "key_infra_splunk-sfdc": {
        "children": [],
        "hosts": [
            "10.219.29.254",
            "10.219.25.147",
            "10.219.161.118",
            "10.219.152.52",
            "10.219.188.151",
            "10.219.114.174"
        ],
        "vars": {}
    },
    "key_infra_spm1": {
        "children": [],
        "hosts": [
            "10.219.31.47",
            "10.219.128.227",
            "10.219.173.45",
            "10.219.107.101",
            "10.219.91.14",
            "10.219.65.35",
            "54.84.207.241",
            "54.85.34.98",
            "54.84.245.20",
            "54.84.191.190"
        ],
        "vars": {}
    },
    "key_infra_stackmakr-ops-blue": {
        "children": [],
        "hosts": [
            "10.219.14.89",
            "54.208.96.71"
        ],
        "vars": {}
    },
    "key_infra_take2": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "10.219.47.252",
            "10.219.53.81",
            "10.219.134.206",
            "10.219.86.78",
            "10.219.92.102",
            "54.84.92.185",
            "54.84.84.233",
            "54.84.87.73",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "key_infra_trial605": {
        "children": [],
        "hosts": [
            "10.219.39.9",
            "10.219.26.28",
            "10.219.60.102",
            "10.219.178.85",
            "10.219.108.141",
            "10.219.81.29",
            "54.86.57.201",
            "54.85.14.238",
            "54.85.75.200",
            "54.86.40.17"
        ],
        "vars": {}
    },
    "key_infra_trial606": {
        "children": [],
        "hosts": [
            "10.219.11.70",
            "10.219.5.147",
            "10.219.16.66",
            "10.219.158.176",
            "10.219.142.79",
            "10.219.100.175",
            "54.85.87.129",
            "54.84.163.82",
            "54.208.228.127",
            "54.84.251.0"
        ],
        "vars": {}
    },
    "key_infra_trial607": {
        "children": [],
        "hosts": [
            "10.219.62.192",
            "10.219.41.67",
            "10.219.18.78",
            "10.219.185.71",
            "10.219.147.74",
            "10.219.98.173",
            "54.86.90.15",
            "54.86.90.142",
            "54.86.90.152",
            "54.86.90.177"
        ],
        "vars": {}
    },
    "key_infra_trial608": {
        "children": [],
        "hosts": [
            "54.85.161.87",
            "54.85.90.7",
            "54.208.59.237",
            "54.85.199.140"
        ],
        "vars": {}
    },
    "key_infra_trial609": {
        "children": [],
        "hosts": [
            "10.219.17.208",
            "10.219.185.186",
            "10.219.154.115",
            "10.219.155.180",
            "10.219.103.150",
            "10.219.67.120",
            "54.208.141.20",
            "54.209.120.55",
            "54.208.210.176",
            "54.209.108.61"
        ],
        "vars": {}
    },
    "key_infra_trial610": {
        "children": [],
        "hosts": [
            "54.84.169.33",
            "54.209.106.125",
            "54.84.240.188",
            "54.84.192.78"
        ],
        "vars": {}
    },
    "key_infra_trial611": {
        "children": [],
        "hosts": [
            "10.219.56.242",
            "10.219.30.68",
            "10.219.57.108",
            "10.219.133.48",
            "10.219.89.90",
            "10.219.111.113",
            "54.84.21.94",
            "54.85.48.128",
            "54.85.208.32",
            "54.85.27.197"
        ],
        "vars": {}
    },
    "key_infra_trial612": {
        "children": [],
        "hosts": [
            "10.219.36.102",
            "10.219.11.190",
            "10.219.140.138",
            "10.219.178.84",
            "10.219.155.123",
            "10.219.90.205",
            "54.85.53.185",
            "54.86.75.36",
            "54.84.114.2",
            "54.86.76.41"
        ],
        "vars": {}
    },
    "key_infra_trial613": {
        "children": [],
        "hosts": [
            "10.219.16.89",
            "10.219.149.40",
            "10.219.142.242",
            "10.219.114.207",
            "10.219.79.196",
            "10.219.85.43",
            "54.86.102.132",
            "54.86.110.180",
            "54.86.110.115",
            "54.86.52.195"
        ],
        "vars": {}
    },
    "key_infra_trial614": {
        "children": [],
        "hosts": [
            "10.219.18.12",
            "10.219.19.226",
            "10.219.180.178",
            "10.219.81.201",
            "10.219.94.27",
            "10.219.117.252",
            "54.86.103.5",
            "54.86.105.40",
            "54.86.104.18",
            "54.86.94.75"
        ],
        "vars": {}
    },
    "key_infra_trial615": {
        "children": [],
        "hosts": [
            "10.219.15.194",
            "10.219.12.146",
            "10.219.138.98",
            "10.219.145.106",
            "10.219.137.205",
            "10.219.86.47",
            "54.85.200.49",
            "54.208.45.55",
            "54.85.95.0",
            "54.85.119.67"
        ],
        "vars": {}
    },
    "key_infra_trial616": {
        "children": [],
        "hosts": [
            "10.219.2.224",
            "10.219.48.124",
            "10.219.154.12",
            "10.219.92.64",
            "10.219.85.31",
            "10.219.89.30",
            "54.209.204.12",
            "54.85.223.164",
            "54.209.14.115",
            "54.209.203.222"
        ],
        "vars": {}
    },
    "key_infra_trial617": {
        "children": [],
        "hosts": [
            "10.219.14.143",
            "10.219.4.55",
            "10.219.130.1",
            "10.219.169.68",
            "10.219.180.244",
            "10.219.122.228",
            "54.84.54.49",
            "54.85.166.231",
            "54.84.245.162",
            "54.85.249.26"
        ],
        "vars": {}
    },
    "key_infra_trial618": {
        "children": [],
        "hosts": [
            "10.219.60.118",
            "10.219.41.191",
            "10.219.41.230",
            "10.219.147.63",
            "10.219.173.37",
            "10.219.64.87",
            "54.86.53.153",
            "54.86.74.37",
            "54.86.81.21",
            "54.86.89.186"
        ],
        "vars": {}
    },
    "key_infra_trial619": {
        "children": [],
        "hosts": [
            "10.219.56.83",
            "10.219.36.162",
            "10.219.45.70",
            "10.219.177.41",
            "10.219.154.211",
            "10.219.96.145",
            "54.86.117.161",
            "54.86.117.163",
            "54.86.117.162",
            "54.86.111.80"
        ],
        "vars": {}
    },
    "key_infra_trial620": {
        "children": [],
        "hosts": [
            "10.219.48.23",
            "10.219.54.28",
            "10.219.143.130",
            "10.219.109.92",
            "10.219.121.80",
            "10.219.109.28",
            "54.85.135.14",
            "54.208.12.112",
            "54.84.103.10",
            "54.209.76.22"
        ],
        "vars": {}
    },
    "key_infra_trial621": {
        "children": [],
        "hosts": [
            "10.219.47.118",
            "10.219.143.228",
            "10.219.187.178",
            "10.219.154.203",
            "10.219.88.75",
            "10.219.97.207",
            "54.209.74.106",
            "54.85.85.59",
            "54.85.48.70",
            "54.208.187.98"
        ],
        "vars": {}
    },
    "key_infra_trial622": {
        "children": [],
        "hosts": [
            "10.219.43.2",
            "10.219.39.144",
            "10.219.63.67",
            "10.219.184.234",
            "10.219.163.166",
            "10.219.68.47",
            "54.209.127.172",
            "54.85.84.167",
            "54.85.47.154",
            "54.209.108.176"
        ],
        "vars": {}
    },
    "key_infra_trial623": {
        "children": [],
        "hosts": [
            "10.219.39.139",
            "10.219.37.47",
            "10.219.25.26",
            "10.219.136.13",
            "10.219.146.42",
            "10.219.78.42",
            "54.85.61.212",
            "54.84.190.144",
            "54.85.255.219",
            "54.85.173.90"
        ],
        "vars": {}
    },
    "key_infra_trial624": {
        "children": [],
        "hosts": [
            "54.84.174.209",
            "54.85.44.185",
            "54.208.89.118",
            "54.85.160.181"
        ],
        "vars": {}
    },
    "key_infra_trial625": {
        "children": [],
        "hosts": [
            "10.219.36.26",
            "10.219.37.213",
            "10.219.142.152",
            "10.219.169.135",
            "10.219.138.185",
            "10.219.111.126",
            "54.86.117.236",
            "54.86.117.237",
            "54.86.116.105",
            "54.86.116.199"
        ],
        "vars": {}
    },
    "key_infra_trial626": {
        "children": [],
        "hosts": [
            "10.219.59.159",
            "10.219.24.179",
            "10.219.9.203",
            "10.219.173.38",
            "10.219.77.13",
            "10.219.66.9",
            "54.86.71.155",
            "54.86.82.149",
            "54.86.77.91",
            "54.86.87.25"
        ],
        "vars": {}
    },
    "key_infra_trial627": {
        "children": [],
        "hosts": [
            "10.219.53.83",
            "10.219.25.150",
            "10.219.128.18",
            "10.219.119.127",
            "10.219.118.148",
            "10.219.109.144",
            "54.86.97.227",
            "54.85.75.4",
            "54.86.97.181",
            "54.86.97.144"
        ],
        "vars": {}
    },
    "key_infra_trial628": {
        "children": [],
        "hosts": [
            "10.219.27.75",
            "10.219.129.154",
            "10.219.155.112",
            "10.219.123.229",
            "10.219.73.211",
            "10.219.114.130",
            "54.86.90.204",
            "54.86.78.51",
            "54.86.92.153",
            "54.86.91.120"
        ],
        "vars": {}
    },
    "key_infra_trial629": {
        "children": [],
        "hosts": [
            "10.219.2.72",
            "10.219.32.78",
            "10.219.63.214",
            "10.219.161.92",
            "10.219.152.253",
            "10.219.75.209",
            "54.86.97.67",
            "54.86.97.73",
            "54.85.196.193",
            "54.86.60.192"
        ],
        "vars": {}
    },
    "key_infra_trial630": {
        "children": [],
        "hosts": [
            "10.219.10.200",
            "10.219.185.101",
            "10.219.163.151",
            "10.219.150.33",
            "10.219.114.210",
            "10.219.75.150",
            "54.85.193.223",
            "54.84.199.152",
            "54.86.55.72",
            "54.86.76.239"
        ],
        "vars": {}
    },
    "key_infra_trial631": {
        "children": [],
        "hosts": [
            "10.219.53.235",
            "10.219.20.248",
            "10.219.27.228",
            "10.219.142.223",
            "10.219.68.180",
            "10.219.78.250",
            "54.86.97.174",
            "54.85.149.164",
            "54.85.207.233",
            "54.86.8.229"
        ],
        "vars": {}
    },
    "key_infra_trial632": {
        "children": [],
        "hosts": [
            "10.219.47.66",
            "10.219.52.205",
            "10.219.137.67",
            "10.219.185.140",
            "10.219.137.49",
            "10.219.110.47",
            "54.86.94.149",
            "54.86.88.52",
            "54.84.81.3",
            "54.86.93.172"
        ],
        "vars": {}
    },
    "key_infra_trial633": {
        "children": [],
        "hosts": [
            "10.219.13.250",
            "10.219.40.153",
            "10.219.5.136",
            "10.219.191.53",
            "10.219.119.27",
            "10.219.68.40",
            "54.86.98.67",
            "54.86.96.151",
            "54.86.99.19",
            "54.86.97.99"
        ],
        "vars": {}
    },
    "key_infra_trial634": {
        "children": [],
        "hosts": [
            "10.219.20.163",
            "10.219.11.33",
            "10.219.136.200",
            "10.219.183.41",
            "10.219.187.219",
            "10.219.97.127",
            "54.86.100.62",
            "54.85.11.117",
            "54.86.98.158",
            "54.86.99.25"
        ],
        "vars": {}
    },
    "key_infra_trial635": {
        "children": [],
        "hosts": [
            "10.219.5.238",
            "10.219.183.205",
            "10.219.134.176",
            "10.219.166.38",
            "10.219.127.169",
            "10.219.91.109",
            "54.86.112.96",
            "54.86.111.172",
            "54.86.111.175",
            "54.86.111.203"
        ],
        "vars": {}
    },
    "key_infra_trial636": {
        "children": [],
        "hosts": [
            "10.219.49.11",
            "10.219.138.5",
            "10.219.153.9",
            "10.219.165.155",
            "10.219.79.157",
            "10.219.121.158",
            "54.86.50.215",
            "54.85.248.82",
            "54.85.170.154",
            "54.85.148.231"
        ],
        "vars": {}
    },
    "key_infra_trial637": {
        "children": [],
        "hosts": [
            "10.219.32.235",
            "10.219.36.177",
            "10.219.159.21",
            "10.219.162.164",
            "10.219.167.0",
            "10.219.115.61",
            "54.86.112.106",
            "54.86.112.102",
            "54.86.3.216",
            "54.86.112.135"
        ],
        "vars": {}
    },
    "key_infra_trial638": {
        "children": [],
        "hosts": [
            "10.219.26.152",
            "10.219.6.136",
            "10.219.63.95",
            "10.219.130.129",
            "10.219.92.4",
            "10.219.68.254",
            "54.86.80.163",
            "54.86.78.119",
            "54.86.80.36",
            "54.86.80.208"
        ],
        "vars": {}
    },
    "key_infra_trial639": {
        "children": [],
        "hosts": [
            "10.219.3.22",
            "10.219.12.138",
            "10.219.18.43",
            "10.219.133.98",
            "10.219.179.156",
            "10.219.119.78",
            "54.86.87.183",
            "54.86.67.89",
            "54.86.104.169",
            "54.86.84.127"
        ],
        "vars": {}
    },
    "key_infra_trial640": {
        "children": [],
        "hosts": [
            "10.219.22.111",
            "10.219.28.211",
            "10.219.142.23",
            "10.219.165.247",
            "10.219.177.177",
            "10.219.78.180",
            "54.86.99.249",
            "54.86.90.71",
            "54.86.101.141",
            "54.86.94.238"
        ],
        "vars": {}
    },
    "key_infra_trial641": {
        "children": [],
        "hosts": [
            "10.219.10.83",
            "10.219.128.183",
            "10.219.158.35",
            "10.219.74.178",
            "10.219.71.164",
            "10.219.66.5",
            "54.84.167.146",
            "54.84.241.208",
            "54.86.61.31",
            "54.86.64.168"
        ],
        "vars": {}
    },
    "key_infra_trial642": {
        "children": [],
        "hosts": [
            "10.219.42.72",
            "10.219.49.157",
            "10.219.9.24",
            "10.219.131.26",
            "10.219.75.107",
            "10.219.77.162",
            "54.86.81.225",
            "54.86.65.171",
            "54.86.60.175",
            "54.86.81.213"
        ],
        "vars": {}
    },
    "key_infra_trial643": {
        "children": [],
        "hosts": [
            "10.219.30.9",
            "10.219.24.227",
            "10.219.175.97",
            "10.219.151.162",
            "10.219.132.1",
            "10.219.97.123",
            "54.86.79.232",
            "54.85.127.222",
            "54.86.45.250",
            "54.86.53.77"
        ],
        "vars": {}
    },
    "key_infra_trial644": {
        "children": [],
        "hosts": [
            "10.219.41.239",
            "10.219.32.15",
            "10.219.175.162",
            "10.219.64.58",
            "10.219.124.145",
            "10.219.125.7",
            "54.86.106.242",
            "54.86.106.241",
            "54.86.106.244",
            "54.86.106.243"
        ],
        "vars": {}
    },
    "key_infra_trial645": {
        "children": [],
        "hosts": [
            "10.219.31.244",
            "10.219.143.239",
            "10.219.140.250",
            "10.219.147.25",
            "10.219.93.219",
            "10.219.101.155",
            "54.86.98.77",
            "54.86.98.21",
            "54.86.38.49",
            "54.85.98.144"
        ],
        "vars": {}
    },
    "key_infra_trial646": {
        "children": [],
        "hosts": [
            "10.219.50.231",
            "10.219.18.88",
            "10.219.62.182",
            "10.219.135.107",
            "10.219.168.254",
            "10.219.89.22",
            "54.86.85.33",
            "54.85.77.167",
            "54.85.251.175",
            "54.86.80.182"
        ],
        "vars": {}
    },
    "key_infra_trial647": {
        "children": [],
        "hosts": [
            "10.219.9.54",
            "10.219.61.3",
            "10.219.156.2",
            "10.219.102.143",
            "10.219.87.56",
            "10.219.67.205",
            "54.86.108.101",
            "54.86.108.102",
            "54.86.108.119",
            "54.86.108.117"
        ],
        "vars": {}
    },
    "key_infra_whisper": {
        "children": [],
        "hosts": [
            "10.219.50.248",
            "10.219.57.225",
            "10.219.33.86",
            "10.219.26.182",
            "10.219.161.181",
            "10.219.164.210",
            "10.217.79.144",
            "54.84.149.25",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com",
            "ec2-50-19-44-148.compute-1.amazonaws.com",
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "key_infra_white-ops": {
        "children": [],
        "hosts": [
            "10.219.6.165",
            "10.219.16.100",
            "10.219.43.249",
            "10.219.157.181",
            "10.219.127.168",
            "10.219.90.31",
            "54.84.148.213",
            "54.84.149.162",
            "54.84.15.178",
            "54.208.10.193"
        ],
        "vars": {}
    },
    "key_infra_zabbix": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12"
        ],
        "vars": {}
    },
    "key_tower": {
        "children": [],
        "hosts": [
            "10.219.129.226",
            "54.86.101.162"
        ],
        "vars": {}
    },
    "security_group_1sot": {
        "children": [],
        "hosts": [
            "ec2-50-19-44-148.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_NAT": {
        "children": [],
        "hosts": [
            "10.219.23.181",
            "10.219.164.166",
            "10.219.123.163",
            "54.208.124.14",
            "54.84.37.150",
            "54.84.41.152"
        ],
        "vars": {}
    },
    "security_group__intermedia": {
        "children": [],
        "hosts": [
            "10.219.17.109",
            "10.219.51.115",
            "10.219.55.210",
            "10.219.41.127",
            "10.219.4.113",
            "10.219.189.219",
            "10.219.152.17",
            "10.219.169.240",
            "10.219.112.253",
            "10.219.64.207",
            "10.219.97.164",
            "10.219.118.126",
            "54.86.85.22",
            "54.84.193.141",
            "54.84.18.13",
            "54.85.193.109",
            "54.86.84.64",
            "54.85.167.62",
            "54.85.126.177",
            "54.86.75.79",
            "54.86.14.157",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "security_group_anaplan_": {
        "children": [],
        "hosts": [
            "10.219.1.219",
            "10.219.49.160",
            "10.219.184.95",
            "10.219.92.107",
            "10.219.117.146",
            "10.219.70.210",
            "54.86.107.51",
            "54.86.125.136",
            "54.86.94.44",
            "54.86.128.114"
        ],
        "vars": {}
    },
    "security_group_backupify": {
        "children": [],
        "hosts": [
            "10.219.5.111",
            "10.219.63.105",
            "10.219.137.105",
            "10.219.168.41",
            "10.219.131.132",
            "10.219.91.234",
            "54.85.54.254",
            "54.85.181.37",
            "54.85.76.42",
            "54.85.68.39"
        ],
        "vars": {}
    },
    "security_group_chef": {
        "children": [],
        "hosts": [
            "10.219.50.248",
            "54.84.149.25"
        ],
        "vars": {}
    },
    "security_group_chef_server": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_climate": {
        "children": [],
        "hosts": [
            "10.219.147.195",
            "54.84.164.51"
        ],
        "vars": {}
    },
    "security_group_cluster-master": {
        "children": [],
        "hosts": [
            "10.219.52.143",
            "10.219.16.100",
            "10.219.130.240",
            "10.219.137.198",
            "10.219.181.82",
            "10.219.168.89",
            "10.219.179.164",
            "10.219.171.92",
            "10.219.107.232",
            "10.219.118.63",
            "54.84.156.145",
            "54.86.39.175",
            "54.84.222.7"
        ],
        "vars": {}
    },
    "security_group_default": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.84.41.152",
            "54.84.65.195",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.28.140",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.37.150",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.189.190",
            "54.84.122.210",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.75.99",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.86.101.162",
            "54.208.124.14",
            "54.208.96.71",
            "54.84.92.185",
            "54.84.42.12",
            "54.84.148.213",
            "54.84.149.25",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.86.23.145",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.217.79.144",
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.123.163",
            "10.219.92.102",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.119.218",
            "10.219.92.169",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.115.77",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.107.101",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.112.202",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.118.52",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.164.166",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.131.132",
            "10.219.160.142",
            "10.219.179.119",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.136.115",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.132.135",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.164.210",
            "10.219.161.181",
            "10.219.144.224",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.129.226",
            "10.219.142.198",
            "10.219.152.142",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.23.181",
            "10.219.14.89",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.61.154",
            "10.219.43.120",
            "10.219.26.182",
            "10.219.33.86",
            "10.219.57.225",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.50.248",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.26.121",
            "10.219.59.57",
            "10.219.41.51",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.12.148",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.25.147",
            "10.219.29.254",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "security_group_defensenet": {
        "children": [],
        "hosts": [
            "10.219.18.251",
            "10.219.107.166",
            "54.84.217.136",
            "54.85.42.39"
        ],
        "vars": {}
    },
    "security_group_fido": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_fidoplus": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_finra_cm": {
        "children": [],
        "hosts": [
            "10.219.52.143",
            "54.84.156.145"
        ],
        "vars": {}
    },
    "security_group_finra_lm": {
        "children": [],
        "hosts": [
            "10.219.173.93",
            "54.84.122.210"
        ],
        "vars": {}
    },
    "security_group_finra_sh": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "10.219.68.240",
            "54.84.152.213"
        ],
        "vars": {}
    },
    "security_group_funtomic-prod": {
        "children": [],
        "hosts": [
            "10.219.28.78",
            "10.219.190.234",
            "10.219.186.145",
            "10.219.168.89",
            "10.219.113.16",
            "54.85.13.176",
            "54.84.137.179",
            "54.84.222.25"
        ],
        "vars": {}
    },
    "security_group_gilt": {
        "children": [],
        "hosts": [
            "10.219.8.78",
            "10.219.59.221",
            "10.219.38.61",
            "10.219.62.128",
            "10.219.167.28",
            "10.219.165.216",
            "10.219.156.153",
            "10.219.67.44",
            "10.219.82.113",
            "54.209.162.114",
            "54.209.183.210",
            "54.85.80.156",
            "54.84.31.76",
            "54.85.52.37",
            "54.85.47.190",
            "54.209.177.56"
        ],
        "vars": {}
    },
    "security_group_idexx": {
        "children": [],
        "hosts": [
            "10.219.60.213",
            "10.219.153.220",
            "10.219.154.94",
            "10.219.130.229",
            "10.219.72.134",
            "10.219.94.77",
            "54.84.46.105",
            "54.85.91.87",
            "54.84.190.109",
            "54.85.148.101"
        ],
        "vars": {}
    },
    "security_group_indexer": {
        "children": [],
        "hosts": [
            "54.208.10.193",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.170.133",
            "54.84.74.125",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.99",
            "54.84.189.190",
            "54.84.137.179",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.84.47.238",
            "54.84.148.213",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.103.231",
            "54.85.13.176",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "10.219.90.31",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.81.15",
            "10.219.126.78",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.157.181",
            "10.219.132.7",
            "10.219.136.17",
            "10.219.145.78",
            "10.219.186.145",
            "10.219.189.153",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.130.190",
            "10.219.6.165",
            "10.219.4.181",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.25.43",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.63.147",
            "10.219.43.57"
        ],
        "vars": {}
    },
    "security_group_jenkins-blue": {
        "children": [],
        "hosts": [
            "10.219.14.89",
            "54.208.96.71"
        ],
        "vars": {}
    },
    "security_group_jenkins-executor": {
        "children": [],
        "hosts": [
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_jenkins-master": {
        "children": [],
        "hosts": [
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_k14": {
        "children": [],
        "hosts": [
            "10.219.35.86",
            "10.219.9.213",
            "10.219.141.55",
            "10.219.134.179",
            "10.219.155.57",
            "10.219.83.87",
            "54.84.156.195",
            "54.86.54.174",
            "54.85.37.235",
            "54.85.175.102"
        ],
        "vars": {}
    },
    "security_group_license-master": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "10.219.12.85",
            "10.219.48.166",
            "10.219.16.141",
            "10.219.1.9",
            "10.219.43.249",
            "10.219.146.30",
            "10.219.190.234",
            "10.219.173.93",
            "10.219.98.192",
            "54.84.23.79",
            "54.84.122.210",
            "54.84.206.192"
        ],
        "vars": {}
    },
    "security_group_lyft": {
        "children": [],
        "hosts": [
            "10.219.29.108",
            "10.219.3.208",
            "10.219.56.12",
            "10.219.184.152",
            "10.219.93.172",
            "10.219.103.216",
            "54.85.42.61",
            "54.208.87.90",
            "54.85.102.208",
            "54.209.139.239"
        ],
        "vars": {}
    },
    "security_group_mckesson": {
        "children": [],
        "hosts": [
            "10.219.43.48",
            "10.219.132.76",
            "10.219.147.27",
            "10.219.95.221",
            "10.219.64.89",
            "10.219.85.120",
            "54.86.141.183",
            "54.86.141.184",
            "54.86.141.187",
            "54.86.103.185"
        ],
        "vars": {}
    },
    "security_group_mckesson_sh": {
        "children": [],
        "hosts": [
            "10.219.95.221"
        ],
        "vars": {}
    },
    "security_group_mindtouch": {
        "children": [],
        "hosts": [
            "10.219.51.0",
            "10.219.152.142",
            "10.219.165.236",
            "10.219.136.115",
            "10.219.72.12",
            "10.219.69.7",
            "10.219.101.208",
            "54.86.119.45",
            "54.86.109.129",
            "54.86.109.121",
            "54.86.112.246"
        ],
        "vars": {}
    },
    "security_group_motionsoft": {
        "children": [],
        "hosts": [
            "10.219.40.115",
            "10.219.49.237",
            "10.219.188.5",
            "10.219.112.202",
            "10.219.103.26",
            "10.219.81.130",
            "54.85.10.98",
            "54.85.16.252",
            "54.84.228.141",
            "54.85.65.51"
        ],
        "vars": {}
    },
    "security_group_nessus": {
        "children": [],
        "hosts": [
            "ec2-54-237-120-196.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_poc1": {
        "children": [],
        "hosts": [
            "10.219.16.141",
            "10.219.25.43",
            "10.219.189.153",
            "10.219.182.240",
            "10.219.181.82",
            "10.219.81.15",
            "54.85.33.186",
            "54.85.66.59",
            "54.85.52.64",
            "54.85.21.183"
        ],
        "vars": {}
    },
    "security_group_poc2": {
        "children": [],
        "hosts": [
            "10.219.32.233",
            "10.219.131.134",
            "10.219.146.30",
            "10.219.118.63",
            "10.219.85.37",
            "10.219.100.34",
            "54.85.53.103",
            "54.85.32.12",
            "54.85.28.140",
            "54.84.252.121"
        ],
        "vars": {}
    },
    "security_group_poc3": {
        "children": [],
        "hosts": [
            "10.219.48.166",
            "10.219.49.54",
            "10.219.166.184",
            "10.219.85.245",
            "10.219.107.232",
            "10.219.126.78",
            "54.84.84.30",
            "54.85.71.17",
            "54.84.166.253",
            "54.85.71.54"
        ],
        "vars": {}
    },
    "security_group_poc4": {
        "children": [],
        "hosts": [
            "10.219.43.57",
            "10.219.12.85",
            "10.219.137.198",
            "10.219.150.111",
            "10.219.177.243",
            "10.219.72.93",
            "54.85.69.123",
            "54.85.45.216",
            "54.84.170.133"
        ],
        "vars": {}
    },
    "security_group_poc5": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "10.219.63.147",
            "10.219.130.240",
            "10.219.169.253",
            "10.219.130.190",
            "10.219.125.232",
            "54.84.23.79",
            "54.85.80.174",
            "54.86.39.175",
            "54.85.72.146",
            "54.84.47.238",
            "54.84.74.125"
        ],
        "vars": {}
    },
    "security_group_search-head": {
        "children": [],
        "hosts": [
            "54.84.15.178",
            "54.85.28.140",
            "54.84.166.253",
            "54.84.242.116",
            "54.84.199.223",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.69.123",
            "54.85.72.146",
            "54.84.42.12",
            "10.219.127.168",
            "10.219.85.37",
            "10.219.84.105",
            "10.219.85.245",
            "10.219.127.193",
            "10.219.136.66",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.182.240",
            "10.219.150.111",
            "10.219.169.253",
            "10.219.43.120",
            "10.219.26.182",
            "10.219.33.86",
            "10.219.57.225"
        ],
        "vars": {}
    },
    "security_group_security-test": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_security-test_cm": {
        "children": [],
        "hosts": [
            "ec2-54-204-188-107.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_security-test_idx": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_security-test_lm": {
        "children": [],
        "hosts": [
            "ec2-54-205-127-141.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_security-test_sh": {
        "children": [],
        "hosts": [
            "ec2-54-197-167-3.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_skynet": {
        "children": [],
        "hosts": [
            "10.219.0.222",
            "10.219.12.148",
            "10.219.1.1",
            "10.219.173.21",
            "10.219.186.171",
            "10.219.103.178",
            "10.219.115.77",
            "10.219.90.109",
            "10.219.92.169",
            "54.85.146.9",
            "54.84.75.99",
            "54.84.189.79",
            "54.86.51.77",
            "54.85.157.183"
        ],
        "vars": {}
    },
    "security_group_sonos": {
        "children": [],
        "hosts": [
            "10.219.56.91",
            "10.219.56.44",
            "10.219.36.235",
            "10.219.39.194",
            "10.219.154.60",
            "10.219.175.103",
            "10.219.150.186",
            "10.219.84.189",
            "10.219.71.223",
            "54.86.48.214",
            "54.86.80.199",
            "54.86.10.255",
            "54.86.56.174",
            "54.86.89.139",
            "54.86.81.117",
            "54.86.88.208"
        ],
        "vars": {}
    },
    "security_group_splunk-sfdc": {
        "children": [],
        "hosts": [
            "10.219.29.254",
            "10.219.25.147",
            "10.219.161.118",
            "10.219.152.52",
            "10.219.188.151",
            "10.219.114.174"
        ],
        "vars": {}
    },
    "security_group_splunk-support": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_splunk_wideopen": {
        "children": [],
        "hosts": [
            "10.219.14.89",
            "54.208.96.71",
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com",
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_spm1": {
        "children": [],
        "hosts": [
            "10.219.31.47",
            "10.219.128.227",
            "10.219.173.45",
            "10.219.107.101",
            "10.219.91.14",
            "10.219.65.35",
            "54.84.207.241",
            "54.85.34.98",
            "54.84.245.20",
            "54.84.191.190"
        ],
        "vars": {}
    },
    "security_group_ssh": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_stackmakr": {
        "children": [],
        "hosts": [
            "10.219.26.182"
        ],
        "vars": {}
    },
    "security_group_stackmakr-corp": {
        "children": [],
        "hosts": [
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_stackmakr-corp_cm": {
        "children": [],
        "hosts": [
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_stackmakr-corp_lm": {
        "children": [],
        "hosts": [
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_stackmakr-ops-blue": {
        "children": [],
        "hosts": [
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_stackmakr-service": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_take2": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "10.219.47.252",
            "10.219.53.81",
            "10.219.134.206",
            "10.219.86.78",
            "10.219.92.102",
            "54.84.92.185",
            "54.84.84.233",
            "54.84.87.73",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "security_group_tower": {
        "children": [],
        "hosts": [
            "10.219.129.226"
        ],
        "vars": {}
    },
    "security_group_trail615": {
        "children": [],
        "hosts": [
            "10.219.15.194",
            "10.219.12.146",
            "10.219.138.98",
            "10.219.145.106",
            "10.219.137.205",
            "10.219.86.47",
            "54.85.200.49",
            "54.208.45.55",
            "54.85.95.0",
            "54.85.119.67"
        ],
        "vars": {}
    },
    "security_group_trial605": {
        "children": [],
        "hosts": [
            "10.219.39.9",
            "10.219.26.28",
            "10.219.60.102",
            "10.219.178.85",
            "10.219.108.141",
            "10.219.81.29",
            "54.86.57.201",
            "54.85.14.238",
            "54.85.75.200",
            "54.86.40.17"
        ],
        "vars": {}
    },
    "security_group_trial606": {
        "children": [],
        "hosts": [
            "10.219.11.70",
            "10.219.5.147",
            "10.219.16.66",
            "10.219.158.176",
            "10.219.142.79",
            "10.219.100.175",
            "54.85.87.129",
            "54.84.163.82",
            "54.208.228.127",
            "54.84.251.0"
        ],
        "vars": {}
    },
    "security_group_trial608": {
        "children": [],
        "hosts": [
            "54.85.161.87",
            "54.85.90.7",
            "54.208.59.237",
            "54.85.199.140"
        ],
        "vars": {}
    },
    "security_group_trial609": {
        "children": [],
        "hosts": [
            "10.219.17.208",
            "10.219.185.186",
            "10.219.154.115",
            "10.219.155.180",
            "10.219.103.150",
            "10.219.67.120",
            "54.208.141.20",
            "54.209.120.55",
            "54.208.210.176",
            "54.209.108.61"
        ],
        "vars": {}
    },
    "security_group_trial610": {
        "children": [],
        "hosts": [
            "54.84.169.33",
            "54.209.106.125",
            "54.84.240.188",
            "54.84.192.78"
        ],
        "vars": {}
    },
    "security_group_trial611": {
        "children": [],
        "hosts": [
            "10.219.56.242",
            "10.219.30.68",
            "10.219.57.108",
            "10.219.133.48",
            "10.219.89.90",
            "10.219.111.113",
            "54.84.21.94",
            "54.85.48.128",
            "54.85.208.32",
            "54.85.27.197"
        ],
        "vars": {}
    },
    "security_group_trial616": {
        "children": [],
        "hosts": [
            "10.219.2.224",
            "10.219.48.124",
            "10.219.154.12",
            "10.219.92.64",
            "10.219.85.31",
            "10.219.89.30",
            "54.209.204.12",
            "54.85.223.164",
            "54.209.14.115",
            "54.209.203.222"
        ],
        "vars": {}
    },
    "security_group_trial617": {
        "children": [],
        "hosts": [
            "10.219.14.143",
            "10.219.4.55",
            "10.219.130.1",
            "10.219.169.68",
            "10.219.180.244",
            "10.219.122.228",
            "54.84.54.49",
            "54.85.166.231",
            "54.84.245.162",
            "54.85.249.26"
        ],
        "vars": {}
    },
    "security_group_trial620": {
        "children": [],
        "hosts": [
            "10.219.48.23",
            "10.219.54.28",
            "10.219.143.130",
            "10.219.109.92",
            "10.219.121.80",
            "10.219.109.28",
            "54.85.135.14",
            "54.208.12.112",
            "54.84.103.10",
            "54.209.76.22"
        ],
        "vars": {}
    },
    "security_group_trial621": {
        "children": [],
        "hosts": [
            "10.219.47.118",
            "10.219.143.228",
            "10.219.187.178",
            "10.219.154.203",
            "10.219.88.75",
            "10.219.97.207",
            "54.209.74.106",
            "54.85.85.59",
            "54.85.48.70",
            "54.208.187.98"
        ],
        "vars": {}
    },
    "security_group_trial622": {
        "children": [],
        "hosts": [
            "10.219.43.2",
            "10.219.39.144",
            "10.219.63.67",
            "10.219.184.234",
            "10.219.163.166",
            "10.219.68.47",
            "54.209.127.172",
            "54.85.84.167",
            "54.85.47.154",
            "54.209.108.176"
        ],
        "vars": {}
    },
    "security_group_trial623": {
        "children": [],
        "hosts": [
            "10.219.39.139",
            "10.219.37.47",
            "10.219.25.26",
            "10.219.136.13",
            "10.219.146.42",
            "10.219.78.42",
            "54.85.61.212",
            "54.84.190.144",
            "54.85.255.219",
            "54.85.173.90"
        ],
        "vars": {}
    },
    "security_group_trial624": {
        "children": [],
        "hosts": [
            "54.84.174.209",
            "54.85.44.185",
            "54.208.89.118",
            "54.85.160.181"
        ],
        "vars": {}
    },
    "security_group_trial636": {
        "children": [],
        "hosts": [
            "10.219.49.11",
            "10.219.138.5",
            "10.219.153.9",
            "10.219.165.155",
            "10.219.79.157",
            "10.219.121.158",
            "54.86.50.215",
            "54.85.248.82",
            "54.85.170.154",
            "54.85.148.231"
        ],
        "vars": {}
    },
    "security_group_trials": {
        "children": [],
        "hosts": [
            "54.86.76.41",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.84.114.2",
            "54.86.75.36",
            "54.86.77.91",
            "54.86.99.19",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.85.53.185",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "10.219.90.205",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231"
        ],
        "vars": {}
    },
    "security_group_zabbix-client": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "security_group_zabbix-server": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12",
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_BuildUser_Chris_Boniak": {
        "children": [],
        "hosts": [
            "54.86.128.114",
            "54.86.94.44",
            "54.85.148.101",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.209.139.239",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.76.41",
            "54.84.190.109",
            "54.85.91.87",
            "54.209.106.125",
            "54.85.102.208",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.114.2",
            "54.86.75.36",
            "54.86.125.136",
            "54.84.46.105",
            "54.84.169.33",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.85.53.185",
            "54.86.107.51",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.107.101",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.90.205",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.184.152",
            "10.219.133.48",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.184.95",
            "10.219.60.213",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.57"
        ],
        "vars": {}
    },
    "tag_BuildUser_Joped": {
        "children": [],
        "hosts": [
            "54.85.199.140",
            "54.209.108.61",
            "54.84.251.0",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.14.157",
            "54.86.75.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.208.228.127",
            "54.84.75.99",
            "54.85.75.200",
            "54.85.167.62",
            "54.86.84.64",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.14.238",
            "54.86.57.201",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.152.213",
            "54.85.69.157",
            "10.219.68.240",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.100.175",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.152.142",
            "10.219.17.208",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.4.79",
            "10.219.87.108",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215"
        ],
        "vars": {}
    },
    "tag_BuildUser_Mike_Regan": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.109.121",
            "54.86.103.185",
            "54.86.141.187",
            "54.85.119.67",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.85.175.102",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.109.129",
            "54.86.141.184",
            "54.85.200.49",
            "54.209.204.12",
            "54.84.54.49",
            "54.86.23.145",
            "54.84.156.195",
            "54.86.119.45",
            "54.86.141.183",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.219.119.218",
            "10.219.86.47",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.112.202",
            "10.219.83.87",
            "10.219.160.142",
            "10.219.179.119",
            "10.219.136.115",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.165.236",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.26.121",
            "10.219.59.57",
            "10.219.41.51",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.2.93",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.51.0",
            "10.219.43.48"
        ],
        "vars": {}
    },
    "tag_BuildUser_Ravi_Anandwala": {
        "children": [],
        "hosts": [
            "54.85.148.231",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.85.170.154",
            "54.85.248.82",
            "54.86.77.91",
            "54.86.99.19",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.50.215",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.49.11",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231"
        ],
        "vars": {}
    },
    "tag_BuildUser_bwong": {
        "children": [],
        "hosts": [
            "10.219.29.254",
            "10.219.25.147",
            "10.219.161.118",
            "10.219.152.52",
            "10.219.188.151",
            "10.219.114.174"
        ],
        "vars": {}
    },
    "tag_BuildUser_mloven": {
        "children": [],
        "hosts": [
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.86.88.208",
            "54.86.81.117",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.86.89.139",
            "54.86.56.174",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.132.135",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_CO-920_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.45.160"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_anaplan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.92.107"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_backupify_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.137.105"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_climate_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.171.92"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_defensenet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.183.156"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.52.143",
            "54.84.156.145"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_funtomic-prod_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.168.89"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.59.221"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_idexx_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.130.229"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.41.127"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_k14_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.134.179"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_lyft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.29.108"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_marriott_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.179.164",
            "54.84.222.7"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_mckesson_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.85.120"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.72.12"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_motionsoft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.112.202"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_mregan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.41.51"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_poc1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.181.82"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_poc2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.118.63"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_poc3_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.107.232"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_poc4_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.137.198"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_poc5_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.130.240",
            "54.86.39.175"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_prod-monitor-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.166.102",
            "10.219.132.127",
            "10.219.134.89",
            "10.219.177.248",
            "10.219.144.224"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_security-test_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-54-204-188-107.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.115.77"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.39.194"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_splunk-sfdc_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.152.52"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_spm1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.91.14"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_take2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.53.81"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial605_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.26.28"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial606_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.11.70"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial607_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.41.67"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial609_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.155.180"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial611_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.30.68"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial612_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.140.138"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial613_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.85.43"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial614_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.81.201"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial615_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.137.205"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial616_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.92.64"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial617_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.180.244"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial618_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.60.118"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial619_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.45.70"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial620_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.121.80"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial621_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.143.228"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial622_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.43.2"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial623_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.39.139"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial625_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.169.135"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial626_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.9.203"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial627_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.119.127"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial628_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.123.229"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial629_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.63.214"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial630_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.150.33"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial631_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.27.228"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial632_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.137.67"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial633_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.40.153"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial634_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.187.219"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial635_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.183.205"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial636_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.165.155"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial637_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.162.164"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial638_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.6.136"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial639_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.12.138"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial640_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.165.247"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial641_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.71.164"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial642_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.9.24"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial643_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.151.162"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial644_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.124.145"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial645_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.147.25"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial646_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.62.182"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_trial647_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.87.56"
        ],
        "vars": {}
    },
    "tag_FQDN_c0m1_white-ops_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.16.100"
        ],
        "vars": {}
    },
    "tag_FQDN_chef-corp-dev_fidoplus_splunkwhisper_com": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_chef-sandbox-dev_fidoplus_splunkwhisper_com": {
        "children": [],
        "hosts": [
            "ec2-174-129-105-52.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_exec03_stackmakr-corp_splunkwhisper_com": {
        "children": [],
        "hosts": [
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_CO-920_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.62.215"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_anaplan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.1.219",
            "54.86.107.51"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_backupify_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.63.105",
            "54.85.54.254"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_climate_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.4.181",
            "54.84.99.227"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_defensenet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.18.251",
            "54.84.217.136"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.36.226",
            "54.84.103.231"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_funtomic-prod_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.28.78",
            "54.85.13.176"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.38.61",
            "54.209.183.210"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_idexx_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.60.213",
            "54.84.46.105"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.55.210",
            "54.84.18.13"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_k14_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.35.86",
            "54.84.156.195"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_lyft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.3.208",
            "54.85.42.61"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_marriott_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.11.12",
            "54.84.125.108"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_mckesson_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.43.48",
            "54.86.141.183"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.51.0",
            "54.86.119.45"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_motionsoft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.49.237",
            "54.85.10.98"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_mregan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.59.57"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_poc1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.25.43",
            "54.85.33.186"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_poc2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.32.233",
            "54.85.53.103"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_poc3_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.49.54",
            "54.84.84.30"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_poc4_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.43.57",
            "54.85.69.157"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_poc5_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.63.147",
            "54.85.80.174"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_prod-monitor-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.58.233",
            "10.219.2.175",
            "10.219.4.252",
            "10.219.16.214"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_security-test_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.1.1",
            "54.85.146.9"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.36.235",
            "54.86.10.255"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_splunk-sfdc_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.25.147"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_spm1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.31.47",
            "54.84.207.241"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_take2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "54.84.92.185"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial605_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.60.102",
            "54.85.14.238"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial606_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.16.66",
            "54.84.163.82"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial607_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.18.78",
            "54.86.90.142"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial608_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.85.161.87"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial609_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.17.208",
            "54.208.141.20"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial610_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.84.169.33"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial611_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.57.108",
            "54.85.48.128"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial612_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.11.190",
            "54.85.53.185"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial613_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.16.89",
            "54.86.102.132"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial614_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.18.12",
            "54.86.103.5"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial615_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.12.146",
            "54.85.200.49"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial616_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.2.224",
            "54.209.204.12"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial617_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.14.143",
            "54.84.54.49"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial618_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.41.191",
            "54.86.53.153"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial619_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.36.162",
            "54.86.117.163"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial620_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.48.23",
            "54.85.135.14"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial621_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.47.118",
            "54.209.74.106"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial622_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.63.67",
            "54.85.84.167"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial623_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.37.47",
            "54.85.61.212"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial624_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.84.174.209"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial625_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.37.213",
            "54.86.117.236"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial626_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.24.179",
            "54.86.82.149"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial627_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.53.83",
            "54.86.97.227"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial628_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.27.75",
            "54.86.90.204"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial629_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.32.78",
            "54.86.97.73"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial630_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.10.200",
            "54.85.193.223"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial631_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.20.248",
            "54.85.149.164"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial632_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.47.66",
            "54.86.94.149"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial633_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.5.136",
            "54.86.96.151"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial634_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.20.163",
            "54.86.100.62"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial635_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.5.238",
            "54.86.112.96"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial636_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.49.11",
            "54.86.50.215"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial637_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.32.235",
            "54.86.112.106"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial638_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.26.152",
            "54.86.80.163"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial639_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.3.22",
            "54.86.87.183"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial640_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.22.111",
            "54.86.99.249"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial641_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.10.83",
            "54.84.167.146"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial642_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.42.72",
            "54.86.81.225"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial643_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.24.227",
            "54.86.79.232"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial644_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.32.15",
            "54.86.106.242"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial645_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.31.244",
            "54.86.98.77"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial646_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.18.88",
            "54.85.77.167"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_trial647_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.61.3",
            "54.86.108.101"
        ],
        "vars": {}
    },
    "tag_FQDN_idx1_white-ops_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.6.165",
            "54.84.148.213"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_CO-920_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.87.108"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_anaplan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.70.210",
            "54.86.128.114"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_backupify_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.91.234",
            "54.85.68.39"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_climate_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.68.99",
            "54.84.142.102"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_defensenet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.107.166",
            "54.85.42.39"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.127.143",
            "54.84.189.117"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_funtomic-prod_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.113.16",
            "54.84.222.25"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.82.113",
            "54.209.177.56"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_idexx_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.72.134",
            "54.85.148.101"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.118.126",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_k14_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.83.87",
            "54.85.175.102"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_lyft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.103.216",
            "54.209.139.239"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_marriott_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.105.247",
            "54.84.185.247"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_mckesson_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.64.89",
            "54.86.103.185"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.69.7",
            "54.86.109.121"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_motionsoft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.103.26",
            "54.84.228.141"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_mregan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_poc1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.81.15",
            "54.85.21.183"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_poc2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.100.34",
            "54.84.252.121"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_poc3_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.126.78",
            "54.85.71.54"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_poc4_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.72.93",
            "54.84.170.133"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_poc5_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.125.232",
            "54.84.74.125"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_prod-monitor-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.114.9",
            "10.219.120.83",
            "10.219.80.212",
            "10.219.120.23",
            "10.219.78.69",
            "10.219.64.217"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_security-test_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-23-22-96-198.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.90.109",
            "54.85.157.183"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.84.189",
            "54.86.81.117"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_splunk-sfdc_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.114.174"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_spm1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.65.35",
            "54.84.191.190"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_take2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.86.78",
            "54.84.87.73"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial605_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.81.29",
            "54.86.40.17"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial606_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.100.175",
            "54.84.251.0"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial607_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.98.173",
            "54.86.90.177"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial608_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.85.199.140"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial609_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.67.120",
            "54.209.108.61"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial610_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.84.192.78"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial611_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.89.90",
            "54.85.27.197"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial612_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.90.205",
            "54.86.76.41"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial613_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.114.207",
            "54.86.110.115"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial614_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.94.27",
            "54.86.104.18"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial615_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.86.47",
            "54.85.119.67"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial616_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.89.30",
            "54.209.203.222"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial617_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.122.228",
            "54.85.249.26"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial618_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.64.87",
            "54.86.89.186"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial619_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.96.145",
            "54.86.111.80"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial620_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.109.92",
            "54.84.103.10"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial621_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.88.75",
            "54.208.187.98"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial622_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.68.47",
            "54.209.108.176"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial623_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.78.42",
            "54.85.173.90"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial624_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.85.160.181"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial625_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.111.126",
            "54.86.116.199"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial626_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.77.13",
            "54.86.87.25"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial627_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.118.148",
            "54.86.97.181"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial628_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.73.211",
            "54.86.92.153"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial629_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.75.209",
            "54.86.60.192"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial630_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.114.210",
            "54.86.76.239"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial631_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.78.250",
            "54.86.8.229"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial632_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.110.47",
            "54.86.93.172"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial633_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.68.40",
            "54.86.97.99"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial634_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.97.127",
            "54.86.99.25"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial635_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.91.109",
            "54.86.111.203"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial636_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.121.158",
            "54.85.148.231"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial637_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.115.61",
            "54.86.112.135"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial638_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.92.4",
            "54.86.80.208"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial639_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.119.78",
            "54.86.84.127"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial640_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.78.180",
            "54.86.94.238"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial641_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.66.5",
            "54.86.64.168"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial642_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.75.107",
            "54.86.81.213"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial643_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.97.123",
            "54.86.53.77"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial644_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.125.7",
            "54.86.106.243"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial645_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.93.219",
            "54.85.98.144"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial646_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.89.22",
            "54.86.80.182"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_trial647_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.102.143",
            "54.86.108.119"
        ],
        "vars": {}
    },
    "tag_FQDN_idx2_white-ops_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.90.31",
            "54.208.10.193"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_CO-920_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.147.76"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_anaplan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.184.95",
            "54.86.125.136"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_backupify_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.168.41",
            "54.85.181.37"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_climate_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.132.7",
            "54.84.155.209"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_defensenet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.174.165",
            "54.84.116.38"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.145.78",
            "54.84.189.190"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_funtomic-prod_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.186.145",
            "54.84.137.179"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.156.153",
            "54.85.52.37"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_idexx_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.153.220",
            "54.85.91.87"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.169.240",
            "54.85.126.177"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_k14_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.155.57",
            "54.85.37.235"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_lyft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.184.152",
            "54.85.102.208"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_marriott_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.136.17",
            "54.84.164.99"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_mckesson_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.147.27",
            "54.86.141.184"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.165.236",
            "54.86.109.129"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_motionsoft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.188.5",
            "54.85.16.252"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_mregan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.179.119"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_poc1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.189.153",
            "54.85.66.59"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_poc2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.131.134",
            "54.85.32.12"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_poc3_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.166.184",
            "54.85.71.17"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_poc4_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.177.243",
            "54.85.45.216"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_poc5_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.130.190",
            "54.84.47.238"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_prod-monitor-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.174.231",
            "10.219.130.19",
            "10.219.148.67",
            "10.219.182.219",
            "10.219.177.150"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.186.171",
            "54.84.189.79"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.150.186",
            "54.86.89.139"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_splunk-sfdc_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.188.151"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_spm1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.173.45",
            "54.85.34.98"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_take2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.134.206",
            "54.84.84.233"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial605_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.178.85",
            "54.85.75.200"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial606_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.142.79",
            "54.208.228.127"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial607_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.147.74",
            "54.86.90.152"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial608_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.208.59.237"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial609_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.185.186",
            "54.209.120.55"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial610_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.209.106.125"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial611_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.133.48",
            "54.85.208.32"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial612_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.178.84",
            "54.86.75.36"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial613_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.149.40",
            "54.86.110.180"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial614_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.180.178",
            "54.86.105.40"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial615_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.145.106",
            "54.85.95.0"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial616_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.12",
            "54.85.223.164"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial617_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.130.1",
            "54.85.166.231"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial618_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.147.63",
            "54.86.81.21"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial619_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.177.41",
            "54.86.117.162"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial620_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.143.130",
            "54.208.12.112"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial621_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.187.178",
            "54.85.85.59"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial622_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.163.166",
            "54.85.47.154"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial623_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.146.42",
            "54.85.255.219"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial624_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.85.44.185"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial625_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.142.152",
            "54.86.117.237"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial626_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.173.38",
            "54.86.77.91"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial627_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.128.18",
            "54.85.75.4"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial628_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.155.112",
            "54.86.78.51"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial629_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.152.253",
            "54.85.196.193"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial630_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.185.101",
            "54.84.199.152"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial631_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.142.223",
            "54.85.207.233"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial632_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.137.49",
            "54.84.81.3"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial633_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.191.53",
            "54.86.99.19"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial634_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.136.200",
            "54.85.11.117"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial635_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.166.38",
            "54.86.111.175"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial636_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.138.5",
            "54.85.248.82"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial637_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.167.0",
            "54.86.3.216"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial638_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.130.129",
            "54.86.80.36"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial639_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.179.156",
            "54.86.104.169"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial640_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.142.23",
            "54.86.90.71"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial641_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.158.35",
            "54.84.241.208"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial642_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.131.26",
            "54.86.60.175"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial643_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.175.97",
            "54.85.127.222"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial644_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.175.162",
            "54.86.106.241"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial645_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.140.250",
            "54.86.38.49"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial646_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.168.254",
            "54.85.251.175"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_trial647_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.156.2",
            "54.86.108.102"
        ],
        "vars": {}
    },
    "tag_FQDN_idx3_white-ops_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.157.181",
            "54.84.149.162"
        ],
        "vars": {}
    },
    "tag_FQDN_idx4_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.62.184",
            "54.84.180.204"
        ],
        "vars": {}
    },
    "tag_FQDN_idx4_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.8.78",
            "54.209.162.114"
        ],
        "vars": {}
    },
    "tag_FQDN_idx4_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.17.109",
            "54.86.85.22"
        ],
        "vars": {}
    },
    "tag_FQDN_idx4_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.2.93",
            "54.86.23.145"
        ],
        "vars": {}
    },
    "tag_FQDN_idx4_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.56.91",
            "54.86.48.214"
        ],
        "vars": {}
    },
    "tag_FQDN_idx5_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.98.174",
            "54.84.80.225"
        ],
        "vars": {}
    },
    "tag_FQDN_idx5_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.67.44",
            "54.85.47.190"
        ],
        "vars": {}
    },
    "tag_FQDN_idx5_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.112.253",
            "54.86.75.79"
        ],
        "vars": {}
    },
    "tag_FQDN_idx5_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.103.178",
            "54.86.51.77"
        ],
        "vars": {}
    },
    "tag_FQDN_idx5_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.71.223",
            "54.86.88.208"
        ],
        "vars": {}
    },
    "tag_FQDN_idx6_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.167.28",
            "54.84.31.76"
        ],
        "vars": {}
    },
    "tag_FQDN_idx6_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.189.219",
            "54.86.84.64"
        ],
        "vars": {}
    },
    "tag_FQDN_idx6_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.173.21",
            "54.84.75.99"
        ],
        "vars": {}
    },
    "tag_FQDN_idx6_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.175.103",
            "54.86.56.174"
        ],
        "vars": {}
    },
    "tag_FQDN_idx7_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.51.115",
            "54.84.193.141"
        ],
        "vars": {}
    },
    "tag_FQDN_idx8_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.64.207",
            "54.86.14.157"
        ],
        "vars": {}
    },
    "tag_FQDN_idx9_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.152.17",
            "54.85.167.62"
        ],
        "vars": {}
    },
    "tag_FQDN_jenkins01_stackmakr-corp_splunkwhisper_com": {
        "children": [],
        "hosts": [
            "ec2-54-205-251-95.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_jenkins01_stackmakr-ops-blue_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-54-221-223-232.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_jenkins01_stackmakr-ops-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.26.182"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_CO-920_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.164.5"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_anaplan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.49.160"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_backupify_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.5.111"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_climate_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.1.9"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_defensenet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.84.105"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.173.93",
            "54.84.122.210"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_funtomic-prod_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.190.234"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.165.216"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_idexx_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.94.77"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.97.164"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_k14_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.9.213"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_lyft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.93.172"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_marriott_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.98.192",
            "54.84.206.192"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_mckesson_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.132.76"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.136.115"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_motionsoft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.40.115"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_mregan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.160.142"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_poc1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.16.141"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_poc2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.146.30"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_poc3_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.48.166"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_poc4_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.12.85"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_poc5_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "54.84.23.79"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_prod-monitor-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.111.13",
            "10.219.111.100",
            "10.219.91.91",
            "10.219.118.52",
            "10.219.115.245",
            "10.219.100.237"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_security-test_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-54-205-127-141.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.0.222"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.60"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_splunk-sfdc_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.29.254"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_spm1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.128.227"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_take2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.47.252"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial605_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.108.141"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial606_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.158.176"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial607_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.185.71"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial609_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.103.150"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial611_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.111.113"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial612_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.36.102"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial613_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.142.242"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial614_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.19.226"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial615_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.15.194"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial616_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.48.124"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial617_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.4.55"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial618_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.173.37"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial619_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.211"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial620_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.54.28"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial621_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.97.207"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial622_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.184.234"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial623_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.136.13"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial625_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.36.26"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial626_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.66.9"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial627_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.25.150"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial628_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.129.154"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial629_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.161.92"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial630_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.75.150"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial631_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.68.180"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial632_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.52.205"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial633_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.119.27"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial634_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.11.33"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial635_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.127.169"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial636_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.79.157"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial637_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.36.177"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial638_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.68.254"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial639_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.133.98"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial640_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.28.211"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial641_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.128.183"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial642_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.77.162"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial643_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.30.9"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial644_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.41.239"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial645_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.101.155"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial646_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.135.107"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_trial647_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.9.54"
        ],
        "vars": {}
    },
    "tag_FQDN_lm1_white-ops_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.43.249"
        ],
        "vars": {}
    },
    "tag_FQDN_ops-blue-exec01_stackmakr-ops-blue_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-54-204-191-195.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_ops-blue-exec02_stackmakr-ops-blue_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-50-17-62-124.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_ops-red-exec01_stackmakr-ops-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.33.86"
        ],
        "vars": {}
    },
    "tag_FQDN_ops-red-exec02_stackmakr-ops-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.57.225"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_CO-920_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.10.116"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_anaplan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.117.146",
            "54.86.94.44"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_backupify_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.131.132",
            "54.85.76.42"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_climate_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.147.195",
            "54.84.164.51"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_defensenet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.184",
            "54.84.97.29"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "54.84.152.213"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_funtomic-prod_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.127.193",
            "54.84.242.116"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_gilt_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.62.128",
            "54.85.80.156"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_idexx_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.94",
            "54.84.190.109"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_intermedia_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.4.113",
            "54.85.193.109"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_k14_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.141.55",
            "54.86.54.174"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_lyft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.56.12",
            "54.208.87.90"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_marriott_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.136.66",
            "54.84.199.223"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_mckesson_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.95.221",
            "54.86.141.187"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.101.208",
            "54.86.112.246"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_motionsoft_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.81.130",
            "54.85.65.51"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_mregan_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.26.121"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_poc1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.182.240",
            "54.85.52.64"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_poc2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.85.37",
            "54.85.28.140"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_poc3_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.85.245",
            "54.84.166.253"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_poc4_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.150.111",
            "54.85.69.123"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_poc5_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.169.253",
            "54.85.72.146"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_prod-monitor-red_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.167.181",
            "10.219.152.208",
            "10.219.161.188",
            "10.219.154.235"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_security-test_splunkcloud_com": {
        "children": [],
        "hosts": [
            "ec2-54-197-167-3.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.92.169"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_sonos_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.56.44",
            "54.86.80.199"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_splunk-sfdc_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.161.118"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_spm1_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.107.101",
            "54.84.245.20"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_take2_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.92.102",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial605_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.39.9",
            "54.86.57.201"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial606_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.5.147",
            "54.85.87.129"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial607_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.62.192",
            "54.86.90.15"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial608_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.85.90.7"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial609_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.115",
            "54.208.210.176"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial610_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.84.240.188"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial611_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.56.242",
            "54.84.21.94"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial612_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.155.123",
            "54.84.114.2"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial613_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.79.196",
            "54.86.52.195"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial614_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.117.252",
            "54.86.94.75"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial615_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.138.98",
            "54.208.45.55"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial616_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.85.31",
            "54.209.14.115"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial617_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.169.68",
            "54.84.245.162"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial618_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.41.230",
            "54.86.74.37"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial619_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.56.83",
            "54.86.117.161"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial620_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.109.28",
            "54.209.76.22"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial621_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.154.203",
            "54.85.48.70"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial622_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.39.144",
            "54.209.127.172"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial623_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.25.26",
            "54.84.190.144"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial624_splunkcloud_com": {
        "children": [],
        "hosts": [
            "54.208.89.118"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial625_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.138.185",
            "54.86.116.105"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial626_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.59.159",
            "54.86.71.155"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial627_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.109.144",
            "54.86.97.144"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial628_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.114.130",
            "54.86.91.120"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial629_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.2.72",
            "54.86.97.67"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial630_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.163.151",
            "54.86.55.72"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial631_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.53.235",
            "54.86.97.174"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial632_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.185.140",
            "54.86.88.52"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial633_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.13.250",
            "54.86.98.67"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial634_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.183.41",
            "54.86.98.158"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial635_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.134.176",
            "54.86.111.172"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial636_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.153.9",
            "54.85.170.154"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial637_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.159.21",
            "54.86.112.102"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial638_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.63.95",
            "54.86.78.119"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial639_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.18.43",
            "54.86.67.89"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial640_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.177.177",
            "54.86.101.141"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial641_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.74.178",
            "54.86.61.31"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial642_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.49.157",
            "54.86.65.171"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial643_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.132.1",
            "54.86.45.250"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial644_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.64.58",
            "54.86.106.244"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial645_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.143.239",
            "54.86.98.21"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial646_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.50.231",
            "54.86.85.33"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_trial647_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.67.205",
            "54.86.108.117"
        ],
        "vars": {}
    },
    "tag_FQDN_sh1_white-ops_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.127.168",
            "54.84.15.178"
        ],
        "vars": {}
    },
    "tag_FQDN_sh2_finra_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.68.240"
        ],
        "vars": {}
    },
    "tag_FQDN_sh2_mindtouch_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.152.142"
        ],
        "vars": {}
    },
    "tag_FQDN_sh2_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.12.148"
        ],
        "vars": {}
    },
    "tag_FQDN_sh3_skynet_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.132.135"
        ],
        "vars": {}
    },
    "tag_FQDN_zabbix1_zabbix_splunkcloud_com": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12"
        ],
        "vars": {}
    },
    "tag_License_whisper-project-test": {
        "children": [],
        "hosts": [
            "ec2-54-205-127-141.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_1sot": {
        "children": [],
        "hosts": [
            "ec2-50-19-44-148.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_CO-920_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.45.160"
        ],
        "vars": {}
    },
    "tag_Name_CO-920_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.62.215"
        ],
        "vars": {}
    },
    "tag_Name_CO-920_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.87.108"
        ],
        "vars": {}
    },
    "tag_Name_CO-920_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.147.76"
        ],
        "vars": {}
    },
    "tag_Name_CO-920_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.164.5"
        ],
        "vars": {}
    },
    "tag_Name_CO-920_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.10.116"
        ],
        "vars": {}
    },
    "tag_Name_anaplan_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.92.107"
        ],
        "vars": {}
    },
    "tag_Name_anaplan_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.1.219",
            "54.86.107.51"
        ],
        "vars": {}
    },
    "tag_Name_anaplan_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.70.210",
            "54.86.128.114"
        ],
        "vars": {}
    },
    "tag_Name_anaplan_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.184.95",
            "54.86.125.136"
        ],
        "vars": {}
    },
    "tag_Name_anaplan_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.49.160"
        ],
        "vars": {}
    },
    "tag_Name_anaplan_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.117.146",
            "54.86.94.44"
        ],
        "vars": {}
    },
    "tag_Name_backupify_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.137.105"
        ],
        "vars": {}
    },
    "tag_Name_backupify_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.63.105",
            "54.85.54.254"
        ],
        "vars": {}
    },
    "tag_Name_backupify_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.91.234",
            "54.85.68.39"
        ],
        "vars": {}
    },
    "tag_Name_backupify_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.168.41",
            "54.85.181.37"
        ],
        "vars": {}
    },
    "tag_Name_backupify_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.5.111"
        ],
        "vars": {}
    },
    "tag_Name_backupify_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.131.132",
            "54.85.76.42"
        ],
        "vars": {}
    },
    "tag_Name_chef_-_whisper": {
        "children": [],
        "hosts": [
            "ec2-54-80-236-42.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_climate_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.171.92"
        ],
        "vars": {}
    },
    "tag_Name_climate_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.4.181",
            "54.84.99.227"
        ],
        "vars": {}
    },
    "tag_Name_climate_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.68.99",
            "54.84.142.102"
        ],
        "vars": {}
    },
    "tag_Name_climate_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.132.7",
            "54.84.155.209"
        ],
        "vars": {}
    },
    "tag_Name_climate_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.1.9"
        ],
        "vars": {}
    },
    "tag_Name_climate_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.147.195",
            "54.84.164.51"
        ],
        "vars": {}
    },
    "tag_Name_defensenet_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.183.156"
        ],
        "vars": {}
    },
    "tag_Name_defensenet_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.18.251",
            "54.84.217.136"
        ],
        "vars": {}
    },
    "tag_Name_defensenet_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.107.166",
            "54.85.42.39"
        ],
        "vars": {}
    },
    "tag_Name_defensenet_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.174.165",
            "54.84.116.38"
        ],
        "vars": {}
    },
    "tag_Name_defensenet_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.84.105"
        ],
        "vars": {}
    },
    "tag_Name_defensenet_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.154.184",
            "54.84.97.29"
        ],
        "vars": {}
    },
    "tag_Name_fido_-_zabbix": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_fidoplus_-_chef-corp-dev": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_fidoplus_-_chef-sandbox-dev": {
        "children": [],
        "hosts": [
            "ec2-174-129-105-52.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.52.143",
            "54.84.156.145"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.36.226",
            "54.84.103.231"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.127.143",
            "54.84.189.117"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.145.78",
            "54.84.189.190"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_idx4": {
        "children": [],
        "hosts": [
            "10.219.62.184",
            "54.84.180.204"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_idx5": {
        "children": [],
        "hosts": [
            "10.219.98.174",
            "54.84.80.225"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.173.93",
            "54.84.122.210"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "54.84.152.213"
        ],
        "vars": {}
    },
    "tag_Name_finra_-_sh2": {
        "children": [],
        "hosts": [
            "10.219.68.240"
        ],
        "vars": {}
    },
    "tag_Name_funtomic-prod_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.168.89"
        ],
        "vars": {}
    },
    "tag_Name_funtomic-prod_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.28.78",
            "54.85.13.176"
        ],
        "vars": {}
    },
    "tag_Name_funtomic-prod_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.113.16",
            "54.84.222.25"
        ],
        "vars": {}
    },
    "tag_Name_funtomic-prod_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.186.145",
            "54.84.137.179"
        ],
        "vars": {}
    },
    "tag_Name_funtomic-prod_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.190.234"
        ],
        "vars": {}
    },
    "tag_Name_funtomic-prod_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.127.193",
            "54.84.242.116"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.59.221"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.38.61",
            "54.209.183.210"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.82.113",
            "54.209.177.56"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.156.153",
            "54.85.52.37"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_idx4": {
        "children": [],
        "hosts": [
            "10.219.8.78",
            "54.209.162.114"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_idx5": {
        "children": [],
        "hosts": [
            "10.219.67.44",
            "54.85.47.190"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_idx6": {
        "children": [],
        "hosts": [
            "10.219.167.28",
            "54.84.31.76"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.165.216"
        ],
        "vars": {}
    },
    "tag_Name_gilt_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.62.128",
            "54.85.80.156"
        ],
        "vars": {}
    },
    "tag_Name_idexx_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.130.229"
        ],
        "vars": {}
    },
    "tag_Name_idexx_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.60.213",
            "54.84.46.105"
        ],
        "vars": {}
    },
    "tag_Name_idexx_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.72.134",
            "54.85.148.101"
        ],
        "vars": {}
    },
    "tag_Name_idexx_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.153.220",
            "54.85.91.87"
        ],
        "vars": {}
    },
    "tag_Name_idexx_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.94.77"
        ],
        "vars": {}
    },
    "tag_Name_idexx_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.154.94",
            "54.84.190.109"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.41.127"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.55.210",
            "54.84.18.13"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.118.126",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.169.240",
            "54.85.126.177"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx4": {
        "children": [],
        "hosts": [
            "10.219.17.109",
            "54.86.85.22"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx5": {
        "children": [],
        "hosts": [
            "10.219.112.253",
            "54.86.75.79"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx6": {
        "children": [],
        "hosts": [
            "10.219.189.219",
            "54.86.84.64"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx7": {
        "children": [],
        "hosts": [
            "10.219.51.115",
            "54.84.193.141"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx8": {
        "children": [],
        "hosts": [
            "10.219.64.207",
            "54.86.14.157"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_idx9": {
        "children": [],
        "hosts": [
            "10.219.152.17",
            "54.85.167.62"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.97.164"
        ],
        "vars": {}
    },
    "tag_Name_intermedia_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.4.113",
            "54.85.193.109"
        ],
        "vars": {}
    },
    "tag_Name_k14_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.134.179"
        ],
        "vars": {}
    },
    "tag_Name_k14_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.35.86",
            "54.84.156.195"
        ],
        "vars": {}
    },
    "tag_Name_k14_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.83.87",
            "54.85.175.102"
        ],
        "vars": {}
    },
    "tag_Name_k14_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.155.57",
            "54.85.37.235"
        ],
        "vars": {}
    },
    "tag_Name_k14_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.9.213"
        ],
        "vars": {}
    },
    "tag_Name_k14_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.141.55",
            "54.86.54.174"
        ],
        "vars": {}
    },
    "tag_Name_lyft_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.29.108"
        ],
        "vars": {}
    },
    "tag_Name_lyft_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.3.208",
            "54.85.42.61"
        ],
        "vars": {}
    },
    "tag_Name_lyft_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.103.216",
            "54.209.139.239"
        ],
        "vars": {}
    },
    "tag_Name_lyft_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.184.152",
            "54.85.102.208"
        ],
        "vars": {}
    },
    "tag_Name_lyft_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.93.172"
        ],
        "vars": {}
    },
    "tag_Name_lyft_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.56.12",
            "54.208.87.90"
        ],
        "vars": {}
    },
    "tag_Name_marriott_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.179.164",
            "54.84.222.7"
        ],
        "vars": {}
    },
    "tag_Name_marriott_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.11.12",
            "54.84.125.108"
        ],
        "vars": {}
    },
    "tag_Name_marriott_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.105.247",
            "54.84.185.247"
        ],
        "vars": {}
    },
    "tag_Name_marriott_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.136.17",
            "54.84.164.99"
        ],
        "vars": {}
    },
    "tag_Name_marriott_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.98.192",
            "54.84.206.192"
        ],
        "vars": {}
    },
    "tag_Name_marriott_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.136.66",
            "54.84.199.223"
        ],
        "vars": {}
    },
    "tag_Name_mckesson_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.85.120"
        ],
        "vars": {}
    },
    "tag_Name_mckesson_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.43.48",
            "54.86.141.183"
        ],
        "vars": {}
    },
    "tag_Name_mckesson_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.64.89",
            "54.86.103.185"
        ],
        "vars": {}
    },
    "tag_Name_mckesson_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.147.27",
            "54.86.141.184"
        ],
        "vars": {}
    },
    "tag_Name_mckesson_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.132.76"
        ],
        "vars": {}
    },
    "tag_Name_mckesson_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.95.221",
            "54.86.141.187"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.72.12"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.51.0",
            "54.86.119.45"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.69.7",
            "54.86.109.121"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.165.236",
            "54.86.109.129"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.136.115"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.101.208",
            "54.86.112.246"
        ],
        "vars": {}
    },
    "tag_Name_mindtouch_-_sh2": {
        "children": [],
        "hosts": [
            "10.219.152.142"
        ],
        "vars": {}
    },
    "tag_Name_motionsoft_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.112.202"
        ],
        "vars": {}
    },
    "tag_Name_motionsoft_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.49.237",
            "54.85.10.98"
        ],
        "vars": {}
    },
    "tag_Name_motionsoft_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.103.26",
            "54.84.228.141"
        ],
        "vars": {}
    },
    "tag_Name_motionsoft_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.188.5",
            "54.85.16.252"
        ],
        "vars": {}
    },
    "tag_Name_motionsoft_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.40.115"
        ],
        "vars": {}
    },
    "tag_Name_motionsoft_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.81.130",
            "54.85.65.51"
        ],
        "vars": {}
    },
    "tag_Name_mregan_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.41.51"
        ],
        "vars": {}
    },
    "tag_Name_mregan_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.59.57"
        ],
        "vars": {}
    },
    "tag_Name_mregan_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_Name_mregan_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.179.119"
        ],
        "vars": {}
    },
    "tag_Name_mregan_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.160.142"
        ],
        "vars": {}
    },
    "tag_Name_mregan_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.26.121"
        ],
        "vars": {}
    },
    "tag_Name_nessus": {
        "children": [],
        "hosts": [
            "ec2-54-237-120-196.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_poc1_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.181.82"
        ],
        "vars": {}
    },
    "tag_Name_poc1_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.25.43",
            "54.85.33.186"
        ],
        "vars": {}
    },
    "tag_Name_poc1_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.81.15",
            "54.85.21.183"
        ],
        "vars": {}
    },
    "tag_Name_poc1_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.189.153",
            "54.85.66.59"
        ],
        "vars": {}
    },
    "tag_Name_poc1_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.16.141"
        ],
        "vars": {}
    },
    "tag_Name_poc1_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.182.240",
            "54.85.52.64"
        ],
        "vars": {}
    },
    "tag_Name_poc2_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.118.63"
        ],
        "vars": {}
    },
    "tag_Name_poc2_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.32.233",
            "54.85.53.103"
        ],
        "vars": {}
    },
    "tag_Name_poc2_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.100.34",
            "54.84.252.121"
        ],
        "vars": {}
    },
    "tag_Name_poc2_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.131.134",
            "54.85.32.12"
        ],
        "vars": {}
    },
    "tag_Name_poc2_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.146.30"
        ],
        "vars": {}
    },
    "tag_Name_poc2_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.85.37",
            "54.85.28.140"
        ],
        "vars": {}
    },
    "tag_Name_poc3_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.107.232"
        ],
        "vars": {}
    },
    "tag_Name_poc3_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.49.54",
            "54.84.84.30"
        ],
        "vars": {}
    },
    "tag_Name_poc3_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.126.78",
            "54.85.71.54"
        ],
        "vars": {}
    },
    "tag_Name_poc3_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.166.184",
            "54.85.71.17"
        ],
        "vars": {}
    },
    "tag_Name_poc3_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.48.166"
        ],
        "vars": {}
    },
    "tag_Name_poc3_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.85.245",
            "54.84.166.253"
        ],
        "vars": {}
    },
    "tag_Name_poc4_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.137.198"
        ],
        "vars": {}
    },
    "tag_Name_poc4_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.43.57",
            "54.85.69.157"
        ],
        "vars": {}
    },
    "tag_Name_poc4_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.72.93",
            "54.84.170.133"
        ],
        "vars": {}
    },
    "tag_Name_poc4_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.177.243",
            "54.85.45.216"
        ],
        "vars": {}
    },
    "tag_Name_poc4_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.12.85"
        ],
        "vars": {}
    },
    "tag_Name_poc4_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.150.111",
            "54.85.69.123"
        ],
        "vars": {}
    },
    "tag_Name_poc5_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.130.240",
            "54.86.39.175"
        ],
        "vars": {}
    },
    "tag_Name_poc5_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.63.147",
            "54.85.80.174"
        ],
        "vars": {}
    },
    "tag_Name_poc5_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.125.232",
            "54.84.74.125"
        ],
        "vars": {}
    },
    "tag_Name_poc5_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.130.190",
            "54.84.47.238"
        ],
        "vars": {}
    },
    "tag_Name_poc5_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "54.84.23.79"
        ],
        "vars": {}
    },
    "tag_Name_poc5_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.169.253",
            "54.85.72.146"
        ],
        "vars": {}
    },
    "tag_Name_prod-chef": {
        "children": [],
        "hosts": [
            "10.219.50.248",
            "54.84.149.25"
        ],
        "vars": {}
    },
    "tag_Name_prod-monitor-red_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.166.102",
            "10.219.132.127",
            "10.219.134.89",
            "10.219.177.248",
            "10.219.144.224"
        ],
        "vars": {}
    },
    "tag_Name_prod-monitor-red_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.58.233",
            "10.219.2.175",
            "10.219.4.252",
            "10.219.16.214"
        ],
        "vars": {}
    },
    "tag_Name_prod-monitor-red_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.114.9",
            "10.219.120.83",
            "10.219.80.212",
            "10.219.120.23",
            "10.219.78.69",
            "10.219.64.217"
        ],
        "vars": {}
    },
    "tag_Name_prod-monitor-red_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.174.231",
            "10.219.130.19",
            "10.219.148.67",
            "10.219.182.219",
            "10.219.177.150"
        ],
        "vars": {}
    },
    "tag_Name_prod-monitor-red_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.111.13",
            "10.219.111.100",
            "10.219.91.91",
            "10.219.118.52",
            "10.219.115.245",
            "10.219.100.237"
        ],
        "vars": {}
    },
    "tag_Name_prod-monitor-red_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.167.181",
            "10.219.152.208",
            "10.219.161.188",
            "10.219.154.235"
        ],
        "vars": {}
    },
    "tag_Name_prod_infra_test": {
        "children": [],
        "hosts": [
            "10.217.79.144"
        ],
        "vars": {}
    },
    "tag_Name_sc-vpc-nat": {
        "children": [],
        "hosts": [
            "10.219.23.181",
            "54.208.124.14"
        ],
        "vars": {}
    },
    "tag_Name_sc-vpc-nat__subnet_2_": {
        "children": [],
        "hosts": [
            "10.219.123.163",
            "54.84.41.152"
        ],
        "vars": {}
    },
    "tag_Name_sc-vpc-nat__subnet_3_": {
        "children": [],
        "hosts": [
            "10.219.164.166",
            "54.84.37.150"
        ],
        "vars": {}
    },
    "tag_Name_security-test_-_c0m1": {
        "children": [],
        "hosts": [
            "ec2-54-204-188-107.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_security-test_-_idx1": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_security-test_-_idx2": {
        "children": [],
        "hosts": [
            "ec2-23-22-96-198.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_security-test_-_lm1": {
        "children": [],
        "hosts": [
            "ec2-54-205-127-141.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_security-test_-_sh1": {
        "children": [],
        "hosts": [
            "ec2-54-197-167-3.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.115.77"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.1.1",
            "54.85.146.9"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.90.109",
            "54.85.157.183"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.186.171",
            "54.84.189.79"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_idx4": {
        "children": [],
        "hosts": [
            "10.219.2.93",
            "54.86.23.145"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_idx5": {
        "children": [],
        "hosts": [
            "10.219.103.178",
            "54.86.51.77"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_idx6": {
        "children": [],
        "hosts": [
            "10.219.173.21",
            "54.84.75.99"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.0.222"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.92.169"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_sh2": {
        "children": [],
        "hosts": [
            "10.219.12.148"
        ],
        "vars": {}
    },
    "tag_Name_skynet_-_sh3": {
        "children": [],
        "hosts": [
            "10.219.132.135"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.39.194"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.36.235",
            "54.86.10.255"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.84.189",
            "54.86.81.117"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.150.186",
            "54.86.89.139"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_idx4": {
        "children": [],
        "hosts": [
            "10.219.56.91",
            "54.86.48.214"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_idx5": {
        "children": [],
        "hosts": [
            "10.219.71.223",
            "54.86.88.208"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_idx6": {
        "children": [],
        "hosts": [
            "10.219.175.103",
            "54.86.56.174"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.154.60"
        ],
        "vars": {}
    },
    "tag_Name_sonos_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.56.44",
            "54.86.80.199"
        ],
        "vars": {}
    },
    "tag_Name_splunk-sfdc_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.152.52"
        ],
        "vars": {}
    },
    "tag_Name_splunk-sfdc_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.25.147"
        ],
        "vars": {}
    },
    "tag_Name_splunk-sfdc_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.114.174"
        ],
        "vars": {}
    },
    "tag_Name_splunk-sfdc_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.188.151"
        ],
        "vars": {}
    },
    "tag_Name_splunk-sfdc_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.29.254"
        ],
        "vars": {}
    },
    "tag_Name_splunk-sfdc_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.161.118"
        ],
        "vars": {}
    },
    "tag_Name_spm1_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.91.14"
        ],
        "vars": {}
    },
    "tag_Name_spm1_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.31.47",
            "54.84.207.241"
        ],
        "vars": {}
    },
    "tag_Name_spm1_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.65.35",
            "54.84.191.190"
        ],
        "vars": {}
    },
    "tag_Name_spm1_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.173.45",
            "54.85.34.98"
        ],
        "vars": {}
    },
    "tag_Name_spm1_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.128.227"
        ],
        "vars": {}
    },
    "tag_Name_spm1_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.107.101",
            "54.84.245.20"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-corp_-_exec03": {
        "children": [],
        "hosts": [
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-corp_-_jenkins01": {
        "children": [],
        "hosts": [
            "ec2-54-205-251-95.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-blue_-_jenkins01": {
        "children": [],
        "hosts": [
            "ec2-54-221-223-232.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-blue_-_ops-blue-exec01": {
        "children": [],
        "hosts": [
            "ec2-54-204-191-195.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-blue_-_ops-blue-exec02": {
        "children": [],
        "hosts": [
            "ec2-50-17-62-124.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-blue_-_ops-blue-exec03__vpc_2_": {
        "children": [],
        "hosts": [
            "10.219.14.89",
            "54.208.96.71"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-red_-_jenkins01": {
        "children": [],
        "hosts": [
            "10.219.26.182"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-red_-_ops-red-exec01": {
        "children": [],
        "hosts": [
            "10.219.33.86"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-red_-_ops-red-exec02": {
        "children": [],
        "hosts": [
            "10.219.57.225"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-red_-_ops-red-exec03": {
        "children": [],
        "hosts": [
            "10.219.164.210"
        ],
        "vars": {}
    },
    "tag_Name_stackmakr-ops-red_-_ops-red-exec04": {
        "children": [],
        "hosts": [
            "10.219.161.181"
        ],
        "vars": {}
    },
    "tag_Name_take2_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.53.81"
        ],
        "vars": {}
    },
    "tag_Name_take2_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "54.84.92.185"
        ],
        "vars": {}
    },
    "tag_Name_take2_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.86.78",
            "54.84.87.73"
        ],
        "vars": {}
    },
    "tag_Name_take2_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.134.206",
            "54.84.84.233"
        ],
        "vars": {}
    },
    "tag_Name_take2_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.47.252"
        ],
        "vars": {}
    },
    "tag_Name_take2_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.92.102",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "tag_Name_tower": {
        "children": [],
        "hosts": [
            "10.219.129.226",
            "54.86.101.162"
        ],
        "vars": {}
    },
    "tag_Name_trial605_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.26.28"
        ],
        "vars": {}
    },
    "tag_Name_trial605_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.60.102",
            "54.85.14.238"
        ],
        "vars": {}
    },
    "tag_Name_trial605_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.81.29",
            "54.86.40.17"
        ],
        "vars": {}
    },
    "tag_Name_trial605_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.178.85",
            "54.85.75.200"
        ],
        "vars": {}
    },
    "tag_Name_trial605_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.108.141"
        ],
        "vars": {}
    },
    "tag_Name_trial605_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.39.9",
            "54.86.57.201"
        ],
        "vars": {}
    },
    "tag_Name_trial606_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.11.70"
        ],
        "vars": {}
    },
    "tag_Name_trial606_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.16.66",
            "54.84.163.82"
        ],
        "vars": {}
    },
    "tag_Name_trial606_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.100.175",
            "54.84.251.0"
        ],
        "vars": {}
    },
    "tag_Name_trial606_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.142.79",
            "54.208.228.127"
        ],
        "vars": {}
    },
    "tag_Name_trial606_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.158.176"
        ],
        "vars": {}
    },
    "tag_Name_trial606_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.5.147",
            "54.85.87.129"
        ],
        "vars": {}
    },
    "tag_Name_trial607_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.41.67"
        ],
        "vars": {}
    },
    "tag_Name_trial607_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.18.78",
            "54.86.90.142"
        ],
        "vars": {}
    },
    "tag_Name_trial607_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.98.173",
            "54.86.90.177"
        ],
        "vars": {}
    },
    "tag_Name_trial607_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.147.74",
            "54.86.90.152"
        ],
        "vars": {}
    },
    "tag_Name_trial607_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.185.71"
        ],
        "vars": {}
    },
    "tag_Name_trial607_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.62.192",
            "54.86.90.15"
        ],
        "vars": {}
    },
    "tag_Name_trial608_-_idx1": {
        "children": [],
        "hosts": [
            "54.85.161.87"
        ],
        "vars": {}
    },
    "tag_Name_trial608_-_idx2": {
        "children": [],
        "hosts": [
            "54.85.199.140"
        ],
        "vars": {}
    },
    "tag_Name_trial608_-_idx3": {
        "children": [],
        "hosts": [
            "54.208.59.237"
        ],
        "vars": {}
    },
    "tag_Name_trial608_-_sh1": {
        "children": [],
        "hosts": [
            "54.85.90.7"
        ],
        "vars": {}
    },
    "tag_Name_trial609_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.155.180"
        ],
        "vars": {}
    },
    "tag_Name_trial609_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.17.208",
            "54.208.141.20"
        ],
        "vars": {}
    },
    "tag_Name_trial609_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.67.120",
            "54.209.108.61"
        ],
        "vars": {}
    },
    "tag_Name_trial609_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.185.186",
            "54.209.120.55"
        ],
        "vars": {}
    },
    "tag_Name_trial609_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.103.150"
        ],
        "vars": {}
    },
    "tag_Name_trial609_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.154.115",
            "54.208.210.176"
        ],
        "vars": {}
    },
    "tag_Name_trial610_-_idx1": {
        "children": [],
        "hosts": [
            "54.84.169.33"
        ],
        "vars": {}
    },
    "tag_Name_trial610_-_idx2": {
        "children": [],
        "hosts": [
            "54.84.192.78"
        ],
        "vars": {}
    },
    "tag_Name_trial610_-_idx3": {
        "children": [],
        "hosts": [
            "54.209.106.125"
        ],
        "vars": {}
    },
    "tag_Name_trial610_-_sh1": {
        "children": [],
        "hosts": [
            "54.84.240.188"
        ],
        "vars": {}
    },
    "tag_Name_trial611_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.30.68"
        ],
        "vars": {}
    },
    "tag_Name_trial611_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.57.108",
            "54.85.48.128"
        ],
        "vars": {}
    },
    "tag_Name_trial611_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.89.90",
            "54.85.27.197"
        ],
        "vars": {}
    },
    "tag_Name_trial611_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.133.48",
            "54.85.208.32"
        ],
        "vars": {}
    },
    "tag_Name_trial611_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.111.113"
        ],
        "vars": {}
    },
    "tag_Name_trial611_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.56.242",
            "54.84.21.94"
        ],
        "vars": {}
    },
    "tag_Name_trial612_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.140.138"
        ],
        "vars": {}
    },
    "tag_Name_trial612_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.11.190",
            "54.85.53.185"
        ],
        "vars": {}
    },
    "tag_Name_trial612_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.90.205",
            "54.86.76.41"
        ],
        "vars": {}
    },
    "tag_Name_trial612_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.178.84",
            "54.86.75.36"
        ],
        "vars": {}
    },
    "tag_Name_trial612_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.36.102"
        ],
        "vars": {}
    },
    "tag_Name_trial612_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.155.123",
            "54.84.114.2"
        ],
        "vars": {}
    },
    "tag_Name_trial613_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.85.43"
        ],
        "vars": {}
    },
    "tag_Name_trial613_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.16.89",
            "54.86.102.132"
        ],
        "vars": {}
    },
    "tag_Name_trial613_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.114.207",
            "54.86.110.115"
        ],
        "vars": {}
    },
    "tag_Name_trial613_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.149.40",
            "54.86.110.180"
        ],
        "vars": {}
    },
    "tag_Name_trial613_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.142.242"
        ],
        "vars": {}
    },
    "tag_Name_trial613_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.79.196",
            "54.86.52.195"
        ],
        "vars": {}
    },
    "tag_Name_trial614_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.81.201"
        ],
        "vars": {}
    },
    "tag_Name_trial614_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.18.12",
            "54.86.103.5"
        ],
        "vars": {}
    },
    "tag_Name_trial614_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.94.27",
            "54.86.104.18"
        ],
        "vars": {}
    },
    "tag_Name_trial614_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.180.178",
            "54.86.105.40"
        ],
        "vars": {}
    },
    "tag_Name_trial614_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.19.226"
        ],
        "vars": {}
    },
    "tag_Name_trial614_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.117.252",
            "54.86.94.75"
        ],
        "vars": {}
    },
    "tag_Name_trial615_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.137.205"
        ],
        "vars": {}
    },
    "tag_Name_trial615_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.12.146",
            "54.85.200.49"
        ],
        "vars": {}
    },
    "tag_Name_trial615_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.86.47",
            "54.85.119.67"
        ],
        "vars": {}
    },
    "tag_Name_trial615_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.145.106",
            "54.85.95.0"
        ],
        "vars": {}
    },
    "tag_Name_trial615_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.15.194"
        ],
        "vars": {}
    },
    "tag_Name_trial615_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.138.98",
            "54.208.45.55"
        ],
        "vars": {}
    },
    "tag_Name_trial616_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.92.64"
        ],
        "vars": {}
    },
    "tag_Name_trial616_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.2.224",
            "54.209.204.12"
        ],
        "vars": {}
    },
    "tag_Name_trial616_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.89.30",
            "54.209.203.222"
        ],
        "vars": {}
    },
    "tag_Name_trial616_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.154.12",
            "54.85.223.164"
        ],
        "vars": {}
    },
    "tag_Name_trial616_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.48.124"
        ],
        "vars": {}
    },
    "tag_Name_trial616_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.85.31",
            "54.209.14.115"
        ],
        "vars": {}
    },
    "tag_Name_trial617_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.180.244"
        ],
        "vars": {}
    },
    "tag_Name_trial617_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.14.143",
            "54.84.54.49"
        ],
        "vars": {}
    },
    "tag_Name_trial617_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.122.228",
            "54.85.249.26"
        ],
        "vars": {}
    },
    "tag_Name_trial617_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.130.1",
            "54.85.166.231"
        ],
        "vars": {}
    },
    "tag_Name_trial617_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.4.55"
        ],
        "vars": {}
    },
    "tag_Name_trial617_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.169.68",
            "54.84.245.162"
        ],
        "vars": {}
    },
    "tag_Name_trial618_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.60.118"
        ],
        "vars": {}
    },
    "tag_Name_trial618_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.41.191",
            "54.86.53.153"
        ],
        "vars": {}
    },
    "tag_Name_trial618_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.64.87",
            "54.86.89.186"
        ],
        "vars": {}
    },
    "tag_Name_trial618_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.147.63",
            "54.86.81.21"
        ],
        "vars": {}
    },
    "tag_Name_trial618_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.173.37"
        ],
        "vars": {}
    },
    "tag_Name_trial618_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.41.230",
            "54.86.74.37"
        ],
        "vars": {}
    },
    "tag_Name_trial619_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.45.70"
        ],
        "vars": {}
    },
    "tag_Name_trial619_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.36.162",
            "54.86.117.163"
        ],
        "vars": {}
    },
    "tag_Name_trial619_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.96.145",
            "54.86.111.80"
        ],
        "vars": {}
    },
    "tag_Name_trial619_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.177.41",
            "54.86.117.162"
        ],
        "vars": {}
    },
    "tag_Name_trial619_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.154.211"
        ],
        "vars": {}
    },
    "tag_Name_trial619_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.56.83",
            "54.86.117.161"
        ],
        "vars": {}
    },
    "tag_Name_trial620_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.121.80"
        ],
        "vars": {}
    },
    "tag_Name_trial620_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.48.23",
            "54.85.135.14"
        ],
        "vars": {}
    },
    "tag_Name_trial620_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.109.92",
            "54.84.103.10"
        ],
        "vars": {}
    },
    "tag_Name_trial620_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.143.130",
            "54.208.12.112"
        ],
        "vars": {}
    },
    "tag_Name_trial620_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.54.28"
        ],
        "vars": {}
    },
    "tag_Name_trial620_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.109.28",
            "54.209.76.22"
        ],
        "vars": {}
    },
    "tag_Name_trial621_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.143.228"
        ],
        "vars": {}
    },
    "tag_Name_trial621_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.47.118",
            "54.209.74.106"
        ],
        "vars": {}
    },
    "tag_Name_trial621_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.88.75",
            "54.208.187.98"
        ],
        "vars": {}
    },
    "tag_Name_trial621_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.187.178",
            "54.85.85.59"
        ],
        "vars": {}
    },
    "tag_Name_trial621_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.97.207"
        ],
        "vars": {}
    },
    "tag_Name_trial621_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.154.203",
            "54.85.48.70"
        ],
        "vars": {}
    },
    "tag_Name_trial622_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.43.2"
        ],
        "vars": {}
    },
    "tag_Name_trial622_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.63.67",
            "54.85.84.167"
        ],
        "vars": {}
    },
    "tag_Name_trial622_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.68.47",
            "54.209.108.176"
        ],
        "vars": {}
    },
    "tag_Name_trial622_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.163.166",
            "54.85.47.154"
        ],
        "vars": {}
    },
    "tag_Name_trial622_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.184.234"
        ],
        "vars": {}
    },
    "tag_Name_trial622_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.39.144",
            "54.209.127.172"
        ],
        "vars": {}
    },
    "tag_Name_trial623_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.39.139"
        ],
        "vars": {}
    },
    "tag_Name_trial623_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.37.47",
            "54.85.61.212"
        ],
        "vars": {}
    },
    "tag_Name_trial623_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.78.42",
            "54.85.173.90"
        ],
        "vars": {}
    },
    "tag_Name_trial623_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.146.42",
            "54.85.255.219"
        ],
        "vars": {}
    },
    "tag_Name_trial623_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.136.13"
        ],
        "vars": {}
    },
    "tag_Name_trial623_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.25.26",
            "54.84.190.144"
        ],
        "vars": {}
    },
    "tag_Name_trial624_-_idx1": {
        "children": [],
        "hosts": [
            "54.84.174.209"
        ],
        "vars": {}
    },
    "tag_Name_trial624_-_idx2": {
        "children": [],
        "hosts": [
            "54.85.160.181"
        ],
        "vars": {}
    },
    "tag_Name_trial624_-_idx3": {
        "children": [],
        "hosts": [
            "54.85.44.185"
        ],
        "vars": {}
    },
    "tag_Name_trial624_-_sh1": {
        "children": [],
        "hosts": [
            "54.208.89.118"
        ],
        "vars": {}
    },
    "tag_Name_trial625_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.169.135"
        ],
        "vars": {}
    },
    "tag_Name_trial625_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.37.213",
            "54.86.117.236"
        ],
        "vars": {}
    },
    "tag_Name_trial625_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.111.126",
            "54.86.116.199"
        ],
        "vars": {}
    },
    "tag_Name_trial625_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.142.152",
            "54.86.117.237"
        ],
        "vars": {}
    },
    "tag_Name_trial625_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.36.26"
        ],
        "vars": {}
    },
    "tag_Name_trial625_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.138.185",
            "54.86.116.105"
        ],
        "vars": {}
    },
    "tag_Name_trial626_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.9.203"
        ],
        "vars": {}
    },
    "tag_Name_trial626_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.24.179",
            "54.86.82.149"
        ],
        "vars": {}
    },
    "tag_Name_trial626_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.77.13",
            "54.86.87.25"
        ],
        "vars": {}
    },
    "tag_Name_trial626_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.173.38",
            "54.86.77.91"
        ],
        "vars": {}
    },
    "tag_Name_trial626_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.66.9"
        ],
        "vars": {}
    },
    "tag_Name_trial626_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.59.159",
            "54.86.71.155"
        ],
        "vars": {}
    },
    "tag_Name_trial627_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.119.127"
        ],
        "vars": {}
    },
    "tag_Name_trial627_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.53.83",
            "54.86.97.227"
        ],
        "vars": {}
    },
    "tag_Name_trial627_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.118.148",
            "54.86.97.181"
        ],
        "vars": {}
    },
    "tag_Name_trial627_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.128.18",
            "54.85.75.4"
        ],
        "vars": {}
    },
    "tag_Name_trial627_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.25.150"
        ],
        "vars": {}
    },
    "tag_Name_trial627_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.109.144",
            "54.86.97.144"
        ],
        "vars": {}
    },
    "tag_Name_trial628_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.123.229"
        ],
        "vars": {}
    },
    "tag_Name_trial628_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.27.75",
            "54.86.90.204"
        ],
        "vars": {}
    },
    "tag_Name_trial628_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.73.211",
            "54.86.92.153"
        ],
        "vars": {}
    },
    "tag_Name_trial628_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.155.112",
            "54.86.78.51"
        ],
        "vars": {}
    },
    "tag_Name_trial628_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.129.154"
        ],
        "vars": {}
    },
    "tag_Name_trial628_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.114.130",
            "54.86.91.120"
        ],
        "vars": {}
    },
    "tag_Name_trial629_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.63.214"
        ],
        "vars": {}
    },
    "tag_Name_trial629_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.32.78",
            "54.86.97.73"
        ],
        "vars": {}
    },
    "tag_Name_trial629_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.75.209",
            "54.86.60.192"
        ],
        "vars": {}
    },
    "tag_Name_trial629_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.152.253",
            "54.85.196.193"
        ],
        "vars": {}
    },
    "tag_Name_trial629_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.161.92"
        ],
        "vars": {}
    },
    "tag_Name_trial629_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.2.72",
            "54.86.97.67"
        ],
        "vars": {}
    },
    "tag_Name_trial630_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.150.33"
        ],
        "vars": {}
    },
    "tag_Name_trial630_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.10.200",
            "54.85.193.223"
        ],
        "vars": {}
    },
    "tag_Name_trial630_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.114.210",
            "54.86.76.239"
        ],
        "vars": {}
    },
    "tag_Name_trial630_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.185.101",
            "54.84.199.152"
        ],
        "vars": {}
    },
    "tag_Name_trial630_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.75.150"
        ],
        "vars": {}
    },
    "tag_Name_trial630_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.163.151",
            "54.86.55.72"
        ],
        "vars": {}
    },
    "tag_Name_trial631_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.27.228"
        ],
        "vars": {}
    },
    "tag_Name_trial631_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.20.248",
            "54.85.149.164"
        ],
        "vars": {}
    },
    "tag_Name_trial631_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.78.250",
            "54.86.8.229"
        ],
        "vars": {}
    },
    "tag_Name_trial631_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.142.223",
            "54.85.207.233"
        ],
        "vars": {}
    },
    "tag_Name_trial631_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.68.180"
        ],
        "vars": {}
    },
    "tag_Name_trial631_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.53.235",
            "54.86.97.174"
        ],
        "vars": {}
    },
    "tag_Name_trial632_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.137.67"
        ],
        "vars": {}
    },
    "tag_Name_trial632_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.47.66",
            "54.86.94.149"
        ],
        "vars": {}
    },
    "tag_Name_trial632_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.110.47",
            "54.86.93.172"
        ],
        "vars": {}
    },
    "tag_Name_trial632_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.137.49",
            "54.84.81.3"
        ],
        "vars": {}
    },
    "tag_Name_trial632_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.52.205"
        ],
        "vars": {}
    },
    "tag_Name_trial632_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.185.140",
            "54.86.88.52"
        ],
        "vars": {}
    },
    "tag_Name_trial633_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.40.153"
        ],
        "vars": {}
    },
    "tag_Name_trial633_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.5.136",
            "54.86.96.151"
        ],
        "vars": {}
    },
    "tag_Name_trial633_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.68.40",
            "54.86.97.99"
        ],
        "vars": {}
    },
    "tag_Name_trial633_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.191.53",
            "54.86.99.19"
        ],
        "vars": {}
    },
    "tag_Name_trial633_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.119.27"
        ],
        "vars": {}
    },
    "tag_Name_trial633_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.13.250",
            "54.86.98.67"
        ],
        "vars": {}
    },
    "tag_Name_trial634_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.187.219"
        ],
        "vars": {}
    },
    "tag_Name_trial634_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.20.163",
            "54.86.100.62"
        ],
        "vars": {}
    },
    "tag_Name_trial634_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.97.127",
            "54.86.99.25"
        ],
        "vars": {}
    },
    "tag_Name_trial634_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.136.200",
            "54.85.11.117"
        ],
        "vars": {}
    },
    "tag_Name_trial634_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.11.33"
        ],
        "vars": {}
    },
    "tag_Name_trial634_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.183.41",
            "54.86.98.158"
        ],
        "vars": {}
    },
    "tag_Name_trial635_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.183.205"
        ],
        "vars": {}
    },
    "tag_Name_trial635_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.5.238",
            "54.86.112.96"
        ],
        "vars": {}
    },
    "tag_Name_trial635_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.91.109",
            "54.86.111.203"
        ],
        "vars": {}
    },
    "tag_Name_trial635_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.166.38",
            "54.86.111.175"
        ],
        "vars": {}
    },
    "tag_Name_trial635_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.127.169"
        ],
        "vars": {}
    },
    "tag_Name_trial635_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.134.176",
            "54.86.111.172"
        ],
        "vars": {}
    },
    "tag_Name_trial636_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.165.155"
        ],
        "vars": {}
    },
    "tag_Name_trial636_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.49.11",
            "54.86.50.215"
        ],
        "vars": {}
    },
    "tag_Name_trial636_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.121.158",
            "54.85.148.231"
        ],
        "vars": {}
    },
    "tag_Name_trial636_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.138.5",
            "54.85.248.82"
        ],
        "vars": {}
    },
    "tag_Name_trial636_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.79.157"
        ],
        "vars": {}
    },
    "tag_Name_trial636_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.153.9",
            "54.85.170.154"
        ],
        "vars": {}
    },
    "tag_Name_trial637_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.162.164"
        ],
        "vars": {}
    },
    "tag_Name_trial637_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.32.235",
            "54.86.112.106"
        ],
        "vars": {}
    },
    "tag_Name_trial637_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.115.61",
            "54.86.112.135"
        ],
        "vars": {}
    },
    "tag_Name_trial637_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.167.0",
            "54.86.3.216"
        ],
        "vars": {}
    },
    "tag_Name_trial637_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.36.177"
        ],
        "vars": {}
    },
    "tag_Name_trial637_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.159.21",
            "54.86.112.102"
        ],
        "vars": {}
    },
    "tag_Name_trial638_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.6.136"
        ],
        "vars": {}
    },
    "tag_Name_trial638_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.26.152",
            "54.86.80.163"
        ],
        "vars": {}
    },
    "tag_Name_trial638_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.92.4",
            "54.86.80.208"
        ],
        "vars": {}
    },
    "tag_Name_trial638_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.130.129",
            "54.86.80.36"
        ],
        "vars": {}
    },
    "tag_Name_trial638_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.68.254"
        ],
        "vars": {}
    },
    "tag_Name_trial638_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.63.95",
            "54.86.78.119"
        ],
        "vars": {}
    },
    "tag_Name_trial639_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.12.138"
        ],
        "vars": {}
    },
    "tag_Name_trial639_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.3.22",
            "54.86.87.183"
        ],
        "vars": {}
    },
    "tag_Name_trial639_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.119.78",
            "54.86.84.127"
        ],
        "vars": {}
    },
    "tag_Name_trial639_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.179.156",
            "54.86.104.169"
        ],
        "vars": {}
    },
    "tag_Name_trial639_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.133.98"
        ],
        "vars": {}
    },
    "tag_Name_trial639_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.18.43",
            "54.86.67.89"
        ],
        "vars": {}
    },
    "tag_Name_trial640_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.165.247"
        ],
        "vars": {}
    },
    "tag_Name_trial640_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.22.111",
            "54.86.99.249"
        ],
        "vars": {}
    },
    "tag_Name_trial640_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.78.180",
            "54.86.94.238"
        ],
        "vars": {}
    },
    "tag_Name_trial640_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.142.23",
            "54.86.90.71"
        ],
        "vars": {}
    },
    "tag_Name_trial640_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.28.211"
        ],
        "vars": {}
    },
    "tag_Name_trial640_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.177.177",
            "54.86.101.141"
        ],
        "vars": {}
    },
    "tag_Name_trial641_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.71.164"
        ],
        "vars": {}
    },
    "tag_Name_trial641_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.10.83",
            "54.84.167.146"
        ],
        "vars": {}
    },
    "tag_Name_trial641_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.66.5",
            "54.86.64.168"
        ],
        "vars": {}
    },
    "tag_Name_trial641_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.158.35",
            "54.84.241.208"
        ],
        "vars": {}
    },
    "tag_Name_trial641_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.128.183"
        ],
        "vars": {}
    },
    "tag_Name_trial641_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.74.178",
            "54.86.61.31"
        ],
        "vars": {}
    },
    "tag_Name_trial642_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.9.24"
        ],
        "vars": {}
    },
    "tag_Name_trial642_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.42.72",
            "54.86.81.225"
        ],
        "vars": {}
    },
    "tag_Name_trial642_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.75.107",
            "54.86.81.213"
        ],
        "vars": {}
    },
    "tag_Name_trial642_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.131.26",
            "54.86.60.175"
        ],
        "vars": {}
    },
    "tag_Name_trial642_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.77.162"
        ],
        "vars": {}
    },
    "tag_Name_trial642_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.49.157",
            "54.86.65.171"
        ],
        "vars": {}
    },
    "tag_Name_trial643_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.151.162"
        ],
        "vars": {}
    },
    "tag_Name_trial643_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.24.227",
            "54.86.79.232"
        ],
        "vars": {}
    },
    "tag_Name_trial643_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.97.123",
            "54.86.53.77"
        ],
        "vars": {}
    },
    "tag_Name_trial643_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.175.97",
            "54.85.127.222"
        ],
        "vars": {}
    },
    "tag_Name_trial643_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.30.9"
        ],
        "vars": {}
    },
    "tag_Name_trial643_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.132.1",
            "54.86.45.250"
        ],
        "vars": {}
    },
    "tag_Name_trial644_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.124.145"
        ],
        "vars": {}
    },
    "tag_Name_trial644_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.32.15",
            "54.86.106.242"
        ],
        "vars": {}
    },
    "tag_Name_trial644_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.125.7",
            "54.86.106.243"
        ],
        "vars": {}
    },
    "tag_Name_trial644_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.175.162",
            "54.86.106.241"
        ],
        "vars": {}
    },
    "tag_Name_trial644_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.41.239"
        ],
        "vars": {}
    },
    "tag_Name_trial644_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.64.58",
            "54.86.106.244"
        ],
        "vars": {}
    },
    "tag_Name_trial645_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.147.25"
        ],
        "vars": {}
    },
    "tag_Name_trial645_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.31.244",
            "54.86.98.77"
        ],
        "vars": {}
    },
    "tag_Name_trial645_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.93.219",
            "54.85.98.144"
        ],
        "vars": {}
    },
    "tag_Name_trial645_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.140.250",
            "54.86.38.49"
        ],
        "vars": {}
    },
    "tag_Name_trial645_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.101.155"
        ],
        "vars": {}
    },
    "tag_Name_trial645_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.143.239",
            "54.86.98.21"
        ],
        "vars": {}
    },
    "tag_Name_trial646_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.62.182"
        ],
        "vars": {}
    },
    "tag_Name_trial646_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.18.88",
            "54.85.77.167"
        ],
        "vars": {}
    },
    "tag_Name_trial646_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.89.22",
            "54.86.80.182"
        ],
        "vars": {}
    },
    "tag_Name_trial646_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.168.254",
            "54.85.251.175"
        ],
        "vars": {}
    },
    "tag_Name_trial646_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.135.107"
        ],
        "vars": {}
    },
    "tag_Name_trial646_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.50.231",
            "54.86.85.33"
        ],
        "vars": {}
    },
    "tag_Name_trial647_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.87.56"
        ],
        "vars": {}
    },
    "tag_Name_trial647_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.61.3",
            "54.86.108.101"
        ],
        "vars": {}
    },
    "tag_Name_trial647_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.102.143",
            "54.86.108.119"
        ],
        "vars": {}
    },
    "tag_Name_trial647_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.156.2",
            "54.86.108.102"
        ],
        "vars": {}
    },
    "tag_Name_trial647_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.9.54"
        ],
        "vars": {}
    },
    "tag_Name_trial647_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.67.205",
            "54.86.108.117"
        ],
        "vars": {}
    },
    "tag_Name_white-ops_-_c0m1": {
        "children": [],
        "hosts": [
            "10.219.16.100"
        ],
        "vars": {}
    },
    "tag_Name_white-ops_-_idx1": {
        "children": [],
        "hosts": [
            "10.219.6.165",
            "54.84.148.213"
        ],
        "vars": {}
    },
    "tag_Name_white-ops_-_idx2": {
        "children": [],
        "hosts": [
            "10.219.90.31",
            "54.208.10.193"
        ],
        "vars": {}
    },
    "tag_Name_white-ops_-_idx3": {
        "children": [],
        "hosts": [
            "10.219.157.181",
            "54.84.149.162"
        ],
        "vars": {}
    },
    "tag_Name_white-ops_-_lm1": {
        "children": [],
        "hosts": [
            "10.219.43.249"
        ],
        "vars": {}
    },
    "tag_Name_white-ops_-_sh1": {
        "children": [],
        "hosts": [
            "10.219.127.168",
            "54.84.15.178"
        ],
        "vars": {}
    },
    "tag_Name_zabbix_-_zabbix1": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12"
        ],
        "vars": {}
    },
    "tag_Role_chef_server": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Role_cluster-master": {
        "children": [],
        "hosts": [
            "54.84.222.7",
            "54.86.39.175",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "54.84.156.145",
            "10.219.72.12",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.91.14",
            "10.219.118.63",
            "10.219.107.232",
            "10.219.115.77",
            "10.219.121.80",
            "10.219.92.64",
            "10.219.112.202",
            "10.219.85.43",
            "10.219.81.201",
            "10.219.123.229",
            "10.219.119.127",
            "10.219.71.164",
            "10.219.124.145",
            "10.219.87.56",
            "10.219.171.92",
            "10.219.179.164",
            "10.219.168.89",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.137.198",
            "10.219.130.240",
            "10.219.130.229",
            "10.219.137.105",
            "10.219.155.180",
            "10.219.137.205",
            "10.219.143.228",
            "10.219.180.244",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.134.179",
            "10.219.169.135",
            "10.219.150.33",
            "10.219.187.219",
            "10.219.137.67",
            "10.219.162.164",
            "10.219.183.205",
            "10.219.165.247",
            "10.219.151.162",
            "10.219.147.25",
            "10.219.144.224",
            "10.219.177.248",
            "10.219.53.81",
            "10.219.16.100",
            "10.219.52.143",
            "10.219.41.51",
            "10.219.29.108",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.11.70",
            "10.219.30.68",
            "10.219.59.221",
            "10.219.41.127",
            "10.219.26.28",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.9.203",
            "10.219.63.214",
            "10.219.27.228",
            "10.219.40.153",
            "10.219.41.67",
            "10.219.6.136",
            "10.219.9.24",
            "10.219.12.138",
            "10.219.62.182",
            "10.219.39.194",
            "10.219.134.89",
            "10.219.152.52",
            "10.219.45.160",
            "10.219.132.127",
            "10.219.166.102"
        ],
        "vars": {}
    },
    "tag_Role_indexer": {
        "children": [],
        "hosts": [
            "54.86.109.121",
            "54.86.128.114",
            "54.86.103.185",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.192.78",
            "54.85.119.67",
            "54.209.139.239",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.209.203.222",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.80.182",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.99",
            "54.84.189.190",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.116.38",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.84.47.238",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.75.99",
            "54.85.75.200",
            "54.86.75.36",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "54.84.92.185",
            "54.84.148.213",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.48.128",
            "54.209.183.210",
            "54.209.162.114",
            "54.84.18.13",
            "54.86.23.145",
            "54.85.14.238",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.81.225",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.10.255",
            "54.86.48.214",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.69.7",
            "10.219.70.210",
            "10.219.64.89",
            "10.219.64.217",
            "10.219.78.69",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.81.15",
            "10.219.126.78",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.119.218",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.67.120",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.118.126",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.121.158",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.77.13",
            "10.219.73.211",
            "10.219.75.209",
            "10.219.78.250",
            "10.219.114.210",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.68.40",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.98.173",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.89.22",
            "10.219.102.143",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.132.7",
            "10.219.136.17",
            "10.219.145.78",
            "10.219.186.145",
            "10.219.173.45",
            "10.219.174.165",
            "10.219.189.153",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.130.190",
            "10.219.179.119",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.185.186",
            "10.219.145.106",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.163.166",
            "10.219.154.12",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.133.48",
            "10.219.156.153",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.178.84",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.147.63",
            "10.219.149.40",
            "10.219.177.41",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.137.49",
            "10.219.128.18",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.179.156",
            "10.219.175.97",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.182.219",
            "10.219.61.154",
            "10.219.6.165",
            "10.219.4.181",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.63.147",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.59.57",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.3.208",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.2.224",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.57.108",
            "10.219.38.61",
            "10.219.8.78",
            "10.219.55.210",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.11.190",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.35.86",
            "10.219.41.191",
            "10.219.36.162",
            "10.219.16.89",
            "10.219.37.213",
            "10.219.24.179",
            "10.219.18.12",
            "10.219.32.78",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.20.248",
            "10.219.5.136",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.47.66",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.26.152",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.42.72",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.18.88",
            "10.219.36.235",
            "10.219.56.91",
            "10.219.51.0",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.147.76",
            "10.219.148.67",
            "10.219.188.151",
            "10.219.25.147",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.120.83",
            "10.219.130.19",
            "10.219.2.175",
            "10.219.114.9",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "tag_Role_jenkins-executor": {
        "children": [],
        "hosts": [
            "10.219.57.225",
            "10.219.33.86",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Role_jenkins-master": {
        "children": [],
        "hosts": [
            "10.219.26.182",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Role_license-master": {
        "children": [],
        "hosts": [
            "54.84.206.192",
            "54.84.122.210",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "54.84.23.79",
            "10.219.100.237",
            "10.219.115.245",
            "10.219.98.192",
            "10.219.84.105",
            "10.219.94.77",
            "10.219.103.150",
            "10.219.93.172",
            "10.219.97.207",
            "10.219.111.113",
            "10.219.97.164",
            "10.219.108.141",
            "10.219.118.52",
            "10.219.79.157",
            "10.219.66.9",
            "10.219.75.150",
            "10.219.68.180",
            "10.219.119.27",
            "10.219.127.169",
            "10.219.68.254",
            "10.219.77.162",
            "10.219.101.155",
            "10.219.173.93",
            "10.219.190.234",
            "10.219.128.227",
            "10.219.146.30",
            "10.219.160.142",
            "10.219.136.115",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.158.176",
            "10.219.165.216",
            "10.219.173.37",
            "10.219.142.242",
            "10.219.154.211",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.185.71",
            "10.219.128.183",
            "10.219.133.98",
            "10.219.135.107",
            "10.219.154.60",
            "10.219.132.76",
            "10.219.47.252",
            "10.219.43.249",
            "10.219.1.9",
            "10.219.16.141",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.47.1",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.15.194",
            "10.219.54.28",
            "10.219.48.124",
            "10.219.4.55",
            "10.219.36.102",
            "10.219.9.213",
            "10.219.19.226",
            "10.219.36.26",
            "10.219.25.150",
            "10.219.11.33",
            "10.219.52.205",
            "10.219.36.177",
            "10.219.28.211",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.9.54",
            "10.219.49.160",
            "10.219.91.91",
            "10.219.164.5",
            "10.219.29.254",
            "10.219.111.100",
            "10.219.111.13"
        ],
        "vars": {}
    },
    "tag_Role_search-head": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.94.44",
            "54.86.141.187",
            "54.84.65.195",
            "54.84.15.178",
            "54.85.28.140",
            "54.84.166.253",
            "54.85.65.51",
            "54.84.242.116",
            "54.84.245.20",
            "54.84.240.188",
            "54.209.76.22",
            "54.208.89.118",
            "54.209.14.115",
            "54.86.52.195",
            "54.86.94.75",
            "54.86.91.120",
            "54.86.97.144",
            "54.86.61.31",
            "54.86.106.244",
            "54.86.108.117",
            "54.84.164.51",
            "54.84.199.223",
            "54.84.97.29",
            "54.85.52.64",
            "54.85.69.123",
            "54.85.72.146",
            "54.85.76.42",
            "54.84.190.109",
            "54.208.210.176",
            "54.208.45.55",
            "54.85.48.70",
            "54.84.245.162",
            "54.84.114.2",
            "54.85.170.154",
            "54.86.54.174",
            "54.86.116.105",
            "54.86.55.72",
            "54.86.88.52",
            "54.86.98.158",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.101.141",
            "54.86.45.250",
            "54.86.98.21",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "54.85.90.7",
            "54.208.87.90",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.87.129",
            "54.84.21.94",
            "54.85.80.156",
            "54.85.193.109",
            "54.86.57.201",
            "54.86.74.37",
            "54.86.117.161",
            "54.86.71.155",
            "54.86.97.67",
            "54.86.97.174",
            "54.86.98.67",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.65.171",
            "54.86.67.89",
            "54.86.85.33",
            "54.86.80.199",
            "54.84.152.213",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.117.146",
            "10.219.95.221",
            "10.219.92.102",
            "10.219.127.168",
            "10.219.85.37",
            "10.219.85.245",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.92.169",
            "10.219.107.101",
            "10.219.109.28",
            "10.219.85.31",
            "10.219.79.196",
            "10.219.117.252",
            "10.219.114.130",
            "10.219.109.144",
            "10.219.74.178",
            "10.219.64.58",
            "10.219.67.205",
            "10.219.147.195",
            "10.219.136.66",
            "10.219.154.184",
            "10.219.182.240",
            "10.219.150.111",
            "10.219.169.253",
            "10.219.131.132",
            "10.219.154.94",
            "10.219.154.115",
            "10.219.138.98",
            "10.219.154.203",
            "10.219.169.68",
            "10.219.132.135",
            "10.219.155.123",
            "10.219.153.9",
            "10.219.141.55",
            "10.219.138.185",
            "10.219.163.151",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.134.176",
            "10.219.159.21",
            "10.219.177.177",
            "10.219.132.1",
            "10.219.143.239",
            "10.219.152.142",
            "10.219.154.235",
            "10.219.26.121",
            "10.219.12.148",
            "10.219.56.12",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.5.147",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.4.113",
            "10.219.39.9",
            "10.219.41.230",
            "10.219.56.83",
            "10.219.59.159",
            "10.219.2.72",
            "10.219.53.235",
            "10.219.13.250",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.49.157",
            "10.219.18.43",
            "10.219.50.231",
            "10.219.56.44",
            "10.219.4.79",
            "10.219.161.188",
            "10.219.161.118",
            "10.219.10.116",
            "10.219.152.208",
            "10.219.167.181"
        ],
        "vars": {}
    },
    "tag_Role_zabbix-server": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12",
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Stack_CO-920": {
        "children": [],
        "hosts": [
            "10.219.62.215",
            "10.219.45.160",
            "10.219.10.116",
            "10.219.164.5",
            "10.219.147.76",
            "10.219.87.108"
        ],
        "vars": {}
    },
    "tag_Stack_anaplan": {
        "children": [],
        "hosts": [
            "10.219.1.219",
            "10.219.49.160",
            "10.219.184.95",
            "10.219.92.107",
            "10.219.117.146",
            "10.219.70.210",
            "54.86.107.51",
            "54.86.125.136",
            "54.86.94.44",
            "54.86.128.114"
        ],
        "vars": {}
    },
    "tag_Stack_backupify": {
        "children": [],
        "hosts": [
            "10.219.5.111",
            "10.219.63.105",
            "10.219.137.105",
            "10.219.168.41",
            "10.219.131.132",
            "10.219.91.234",
            "54.85.54.254",
            "54.85.181.37",
            "54.85.76.42",
            "54.85.68.39"
        ],
        "vars": {}
    },
    "tag_Stack_climate": {
        "children": [],
        "hosts": [
            "10.219.1.9",
            "10.219.4.181",
            "10.219.147.195",
            "10.219.132.7",
            "10.219.171.92",
            "10.219.68.99",
            "54.84.99.227",
            "54.84.164.51",
            "54.84.155.209",
            "54.84.142.102"
        ],
        "vars": {}
    },
    "tag_Stack_defensenet": {
        "children": [],
        "hosts": [
            "10.219.18.251",
            "10.219.183.156",
            "10.219.174.165",
            "10.219.154.184",
            "10.219.84.105",
            "10.219.107.166",
            "54.84.217.136",
            "54.84.116.38",
            "54.84.97.29",
            "54.85.42.39"
        ],
        "vars": {}
    },
    "tag_Stack_fido": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Stack_fidoplus": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Stack_finra": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "10.219.36.226",
            "10.219.52.143",
            "10.219.62.184",
            "10.219.173.93",
            "10.219.145.78",
            "10.219.98.174",
            "10.219.127.143",
            "10.219.68.240",
            "54.84.152.213",
            "54.84.103.231",
            "54.84.156.145",
            "54.84.180.204",
            "54.84.122.210",
            "54.84.189.190",
            "54.84.80.225",
            "54.84.189.117"
        ],
        "vars": {}
    },
    "tag_Stack_funtomic-prod": {
        "children": [],
        "hosts": [
            "10.219.28.78",
            "10.219.190.234",
            "10.219.186.145",
            "10.219.168.89",
            "10.219.127.193",
            "10.219.113.16",
            "54.85.13.176",
            "54.84.137.179",
            "54.84.242.116",
            "54.84.222.25"
        ],
        "vars": {}
    },
    "tag_Stack_gilt": {
        "children": [],
        "hosts": [
            "10.219.8.78",
            "10.219.59.221",
            "10.219.38.61",
            "10.219.62.128",
            "10.219.167.28",
            "10.219.165.216",
            "10.219.156.153",
            "10.219.67.44",
            "10.219.82.113",
            "54.209.162.114",
            "54.209.183.210",
            "54.85.80.156",
            "54.84.31.76",
            "54.85.52.37",
            "54.85.47.190",
            "54.209.177.56"
        ],
        "vars": {}
    },
    "tag_Stack_idexx": {
        "children": [],
        "hosts": [
            "10.219.60.213",
            "10.219.153.220",
            "10.219.154.94",
            "10.219.130.229",
            "10.219.72.134",
            "10.219.94.77",
            "54.84.46.105",
            "54.85.91.87",
            "54.84.190.109",
            "54.85.148.101"
        ],
        "vars": {}
    },
    "tag_Stack_intermedia": {
        "children": [],
        "hosts": [
            "10.219.17.109",
            "10.219.51.115",
            "10.219.55.210",
            "10.219.41.127",
            "10.219.4.113",
            "10.219.189.219",
            "10.219.152.17",
            "10.219.169.240",
            "10.219.112.253",
            "10.219.64.207",
            "10.219.97.164",
            "10.219.118.126",
            "54.86.85.22",
            "54.84.193.141",
            "54.84.18.13",
            "54.85.193.109",
            "54.86.84.64",
            "54.85.167.62",
            "54.85.126.177",
            "54.86.75.79",
            "54.86.14.157",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "tag_Stack_k14": {
        "children": [],
        "hosts": [
            "10.219.35.86",
            "10.219.9.213",
            "10.219.141.55",
            "10.219.134.179",
            "10.219.155.57",
            "10.219.83.87",
            "54.84.156.195",
            "54.86.54.174",
            "54.85.37.235",
            "54.85.175.102"
        ],
        "vars": {}
    },
    "tag_Stack_lyft": {
        "children": [],
        "hosts": [
            "10.219.29.108",
            "10.219.3.208",
            "10.219.56.12",
            "10.219.184.152",
            "10.219.93.172",
            "10.219.103.216",
            "54.85.42.61",
            "54.208.87.90",
            "54.85.102.208",
            "54.209.139.239"
        ],
        "vars": {}
    },
    "tag_Stack_marriott": {
        "children": [],
        "hosts": [
            "10.219.11.12",
            "10.219.136.66",
            "10.219.136.17",
            "10.219.179.164",
            "10.219.98.192",
            "10.219.105.247",
            "54.84.125.108",
            "54.84.199.223",
            "54.84.164.99",
            "54.84.222.7",
            "54.84.206.192",
            "54.84.185.247"
        ],
        "vars": {}
    },
    "tag_Stack_mckesson": {
        "children": [],
        "hosts": [
            "10.219.43.48",
            "10.219.132.76",
            "10.219.147.27",
            "10.219.95.221",
            "10.219.64.89",
            "10.219.85.120",
            "54.86.141.183",
            "54.86.141.184",
            "54.86.141.187",
            "54.86.103.185"
        ],
        "vars": {}
    },
    "tag_Stack_mindtouch": {
        "children": [],
        "hosts": [
            "10.219.51.0",
            "10.219.152.142",
            "10.219.165.236",
            "10.219.136.115",
            "10.219.72.12",
            "10.219.69.7",
            "10.219.101.208",
            "54.86.119.45",
            "54.86.109.129",
            "54.86.109.121",
            "54.86.112.246"
        ],
        "vars": {}
    },
    "tag_Stack_motionsoft": {
        "children": [],
        "hosts": [
            "10.219.40.115",
            "10.219.49.237",
            "10.219.188.5",
            "10.219.112.202",
            "10.219.103.26",
            "10.219.81.130",
            "54.85.10.98",
            "54.85.16.252",
            "54.84.228.141",
            "54.85.65.51"
        ],
        "vars": {}
    },
    "tag_Stack_mregan": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_Stack_poc1": {
        "children": [],
        "hosts": [
            "10.219.16.141",
            "10.219.25.43",
            "10.219.189.153",
            "10.219.182.240",
            "10.219.181.82",
            "10.219.81.15",
            "54.85.33.186",
            "54.85.66.59",
            "54.85.52.64",
            "54.85.21.183"
        ],
        "vars": {}
    },
    "tag_Stack_poc2": {
        "children": [],
        "hosts": [
            "10.219.32.233",
            "10.219.131.134",
            "10.219.146.30",
            "10.219.118.63",
            "10.219.85.37",
            "10.219.100.34",
            "54.85.53.103",
            "54.85.32.12",
            "54.85.28.140",
            "54.84.252.121"
        ],
        "vars": {}
    },
    "tag_Stack_poc3": {
        "children": [],
        "hosts": [
            "10.219.48.166",
            "10.219.49.54",
            "10.219.166.184",
            "10.219.85.245",
            "10.219.107.232",
            "10.219.126.78",
            "54.84.84.30",
            "54.85.71.17",
            "54.84.166.253",
            "54.85.71.54"
        ],
        "vars": {}
    },
    "tag_Stack_poc4": {
        "children": [],
        "hosts": [
            "10.219.43.57",
            "10.219.12.85",
            "10.219.137.198",
            "10.219.150.111",
            "10.219.177.243",
            "10.219.72.93",
            "54.85.69.157",
            "54.85.69.123",
            "54.85.45.216",
            "54.84.170.133"
        ],
        "vars": {}
    },
    "tag_Stack_poc5": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "10.219.63.147",
            "10.219.130.240",
            "10.219.169.253",
            "10.219.130.190",
            "10.219.125.232",
            "54.84.23.79",
            "54.85.80.174",
            "54.86.39.175",
            "54.85.72.146",
            "54.84.47.238",
            "54.84.74.125"
        ],
        "vars": {}
    },
    "tag_Stack_prod-monitor-red": {
        "children": [],
        "hosts": [
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.120.23",
            "10.219.118.52",
            "10.219.177.150",
            "10.219.144.224",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.16.214",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "tag_Stack_security-test": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Stack_skynet": {
        "children": [],
        "hosts": [
            "10.219.2.93",
            "10.219.0.222",
            "10.219.12.148",
            "10.219.1.1",
            "10.219.173.21",
            "10.219.132.135",
            "10.219.186.171",
            "10.219.103.178",
            "10.219.115.77",
            "10.219.90.109",
            "10.219.92.169",
            "54.86.23.145",
            "54.85.146.9",
            "54.84.75.99",
            "54.84.189.79",
            "54.86.51.77",
            "54.85.157.183"
        ],
        "vars": {}
    },
    "tag_Stack_sonos": {
        "children": [],
        "hosts": [
            "10.219.56.91",
            "10.219.56.44",
            "10.219.36.235",
            "10.219.39.194",
            "10.219.154.60",
            "10.219.175.103",
            "10.219.150.186",
            "10.219.84.189",
            "10.219.71.223",
            "54.86.48.214",
            "54.86.80.199",
            "54.86.10.255",
            "54.86.56.174",
            "54.86.89.139",
            "54.86.81.117",
            "54.86.88.208"
        ],
        "vars": {}
    },
    "tag_Stack_splunk-sfdc": {
        "children": [],
        "hosts": [
            "10.219.29.254",
            "10.219.25.147",
            "10.219.161.118",
            "10.219.152.52",
            "10.219.188.151",
            "10.219.114.174"
        ],
        "vars": {}
    },
    "tag_Stack_spm1": {
        "children": [],
        "hosts": [
            "10.219.31.47",
            "10.219.128.227",
            "10.219.173.45",
            "10.219.107.101",
            "10.219.91.14",
            "10.219.65.35",
            "54.84.207.241",
            "54.85.34.98",
            "54.84.245.20",
            "54.84.191.190"
        ],
        "vars": {}
    },
    "tag_Stack_stackmakr-corp": {
        "children": [],
        "hosts": [
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Stack_stackmakr-ops-blue": {
        "children": [],
        "hosts": [
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Stack_stackmakr-ops-red": {
        "children": [],
        "hosts": [
            "10.219.57.225",
            "10.219.33.86",
            "10.219.26.182"
        ],
        "vars": {}
    },
    "tag_Stack_take2": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "10.219.47.252",
            "10.219.53.81",
            "10.219.134.206",
            "10.219.86.78",
            "10.219.92.102",
            "54.84.92.185",
            "54.84.84.233",
            "54.84.87.73",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "tag_Stack_trial605": {
        "children": [],
        "hosts": [
            "10.219.39.9",
            "10.219.26.28",
            "10.219.60.102",
            "10.219.178.85",
            "10.219.108.141",
            "10.219.81.29",
            "54.86.57.201",
            "54.85.14.238",
            "54.85.75.200",
            "54.86.40.17"
        ],
        "vars": {}
    },
    "tag_Stack_trial606": {
        "children": [],
        "hosts": [
            "10.219.11.70",
            "10.219.5.147",
            "10.219.16.66",
            "10.219.158.176",
            "10.219.142.79",
            "10.219.100.175",
            "54.85.87.129",
            "54.84.163.82",
            "54.208.228.127",
            "54.84.251.0"
        ],
        "vars": {}
    },
    "tag_Stack_trial607": {
        "children": [],
        "hosts": [
            "10.219.62.192",
            "10.219.41.67",
            "10.219.18.78",
            "10.219.185.71",
            "10.219.147.74",
            "10.219.98.173",
            "54.86.90.15",
            "54.86.90.142",
            "54.86.90.152",
            "54.86.90.177"
        ],
        "vars": {}
    },
    "tag_Stack_trial608": {
        "children": [],
        "hosts": [
            "54.85.161.87",
            "54.85.90.7",
            "54.208.59.237",
            "54.85.199.140"
        ],
        "vars": {}
    },
    "tag_Stack_trial609": {
        "children": [],
        "hosts": [
            "10.219.17.208",
            "10.219.185.186",
            "10.219.154.115",
            "10.219.155.180",
            "10.219.103.150",
            "10.219.67.120",
            "54.208.141.20",
            "54.209.120.55",
            "54.208.210.176",
            "54.209.108.61"
        ],
        "vars": {}
    },
    "tag_Stack_trial610": {
        "children": [],
        "hosts": [
            "54.84.169.33",
            "54.209.106.125",
            "54.84.240.188",
            "54.84.192.78"
        ],
        "vars": {}
    },
    "tag_Stack_trial611": {
        "children": [],
        "hosts": [
            "10.219.56.242",
            "10.219.30.68",
            "10.219.57.108",
            "10.219.133.48",
            "10.219.89.90",
            "10.219.111.113",
            "54.84.21.94",
            "54.85.48.128",
            "54.85.208.32",
            "54.85.27.197"
        ],
        "vars": {}
    },
    "tag_Stack_trial612": {
        "children": [],
        "hosts": [
            "10.219.36.102",
            "10.219.11.190",
            "10.219.140.138",
            "10.219.178.84",
            "10.219.155.123",
            "10.219.90.205",
            "54.85.53.185",
            "54.86.75.36",
            "54.84.114.2",
            "54.86.76.41"
        ],
        "vars": {}
    },
    "tag_Stack_trial613": {
        "children": [],
        "hosts": [
            "10.219.16.89",
            "10.219.149.40",
            "10.219.142.242",
            "10.219.114.207",
            "10.219.79.196",
            "10.219.85.43",
            "54.86.102.132",
            "54.86.110.180",
            "54.86.110.115",
            "54.86.52.195"
        ],
        "vars": {}
    },
    "tag_Stack_trial614": {
        "children": [],
        "hosts": [
            "10.219.18.12",
            "10.219.19.226",
            "10.219.180.178",
            "10.219.81.201",
            "10.219.94.27",
            "10.219.117.252",
            "54.86.103.5",
            "54.86.105.40",
            "54.86.104.18",
            "54.86.94.75"
        ],
        "vars": {}
    },
    "tag_Stack_trial615": {
        "children": [],
        "hosts": [
            "10.219.15.194",
            "10.219.12.146",
            "10.219.138.98",
            "10.219.145.106",
            "10.219.137.205",
            "10.219.86.47",
            "54.85.200.49",
            "54.208.45.55",
            "54.85.95.0",
            "54.85.119.67"
        ],
        "vars": {}
    },
    "tag_Stack_trial616": {
        "children": [],
        "hosts": [
            "10.219.2.224",
            "10.219.48.124",
            "10.219.154.12",
            "10.219.92.64",
            "10.219.85.31",
            "10.219.89.30",
            "54.209.204.12",
            "54.85.223.164",
            "54.209.14.115",
            "54.209.203.222"
        ],
        "vars": {}
    },
    "tag_Stack_trial617": {
        "children": [],
        "hosts": [
            "10.219.14.143",
            "10.219.4.55",
            "10.219.130.1",
            "10.219.169.68",
            "10.219.180.244",
            "10.219.122.228",
            "54.84.54.49",
            "54.85.166.231",
            "54.84.245.162",
            "54.85.249.26"
        ],
        "vars": {}
    },
    "tag_Stack_trial618": {
        "children": [],
        "hosts": [
            "10.219.60.118",
            "10.219.41.191",
            "10.219.41.230",
            "10.219.147.63",
            "10.219.173.37",
            "10.219.64.87",
            "54.86.53.153",
            "54.86.74.37",
            "54.86.81.21",
            "54.86.89.186"
        ],
        "vars": {}
    },
    "tag_Stack_trial619": {
        "children": [],
        "hosts": [
            "10.219.56.83",
            "10.219.36.162",
            "10.219.45.70",
            "10.219.177.41",
            "10.219.154.211",
            "10.219.96.145",
            "54.86.117.161",
            "54.86.117.163",
            "54.86.117.162",
            "54.86.111.80"
        ],
        "vars": {}
    },
    "tag_Stack_trial620": {
        "children": [],
        "hosts": [
            "10.219.48.23",
            "10.219.54.28",
            "10.219.143.130",
            "10.219.109.92",
            "10.219.121.80",
            "10.219.109.28",
            "54.85.135.14",
            "54.208.12.112",
            "54.84.103.10",
            "54.209.76.22"
        ],
        "vars": {}
    },
    "tag_Stack_trial621": {
        "children": [],
        "hosts": [
            "10.219.47.118",
            "10.219.143.228",
            "10.219.187.178",
            "10.219.154.203",
            "10.219.88.75",
            "10.219.97.207",
            "54.209.74.106",
            "54.85.85.59",
            "54.85.48.70",
            "54.208.187.98"
        ],
        "vars": {}
    },
    "tag_Stack_trial622": {
        "children": [],
        "hosts": [
            "10.219.43.2",
            "10.219.39.144",
            "10.219.63.67",
            "10.219.184.234",
            "10.219.163.166",
            "10.219.68.47",
            "54.209.127.172",
            "54.85.84.167",
            "54.85.47.154",
            "54.209.108.176"
        ],
        "vars": {}
    },
    "tag_Stack_trial623": {
        "children": [],
        "hosts": [
            "10.219.39.139",
            "10.219.37.47",
            "10.219.25.26",
            "10.219.136.13",
            "10.219.146.42",
            "10.219.78.42",
            "54.85.61.212",
            "54.84.190.144",
            "54.85.255.219",
            "54.85.173.90"
        ],
        "vars": {}
    },
    "tag_Stack_trial624": {
        "children": [],
        "hosts": [
            "54.84.174.209",
            "54.85.44.185",
            "54.208.89.118",
            "54.85.160.181"
        ],
        "vars": {}
    },
    "tag_Stack_trial625": {
        "children": [],
        "hosts": [
            "10.219.36.26",
            "10.219.37.213",
            "10.219.142.152",
            "10.219.169.135",
            "10.219.138.185",
            "10.219.111.126",
            "54.86.117.236",
            "54.86.117.237",
            "54.86.116.105",
            "54.86.116.199"
        ],
        "vars": {}
    },
    "tag_Stack_trial626": {
        "children": [],
        "hosts": [
            "10.219.59.159",
            "10.219.24.179",
            "10.219.9.203",
            "10.219.173.38",
            "10.219.77.13",
            "10.219.66.9",
            "54.86.71.155",
            "54.86.82.149",
            "54.86.77.91",
            "54.86.87.25"
        ],
        "vars": {}
    },
    "tag_Stack_trial627": {
        "children": [],
        "hosts": [
            "10.219.53.83",
            "10.219.25.150",
            "10.219.128.18",
            "10.219.119.127",
            "10.219.118.148",
            "10.219.109.144",
            "54.86.97.227",
            "54.85.75.4",
            "54.86.97.181",
            "54.86.97.144"
        ],
        "vars": {}
    },
    "tag_Stack_trial628": {
        "children": [],
        "hosts": [
            "10.219.27.75",
            "10.219.129.154",
            "10.219.155.112",
            "10.219.123.229",
            "10.219.73.211",
            "10.219.114.130",
            "54.86.90.204",
            "54.86.78.51",
            "54.86.92.153",
            "54.86.91.120"
        ],
        "vars": {}
    },
    "tag_Stack_trial629": {
        "children": [],
        "hosts": [
            "10.219.2.72",
            "10.219.32.78",
            "10.219.63.214",
            "10.219.161.92",
            "10.219.152.253",
            "10.219.75.209",
            "54.86.97.67",
            "54.86.97.73",
            "54.85.196.193",
            "54.86.60.192"
        ],
        "vars": {}
    },
    "tag_Stack_trial630": {
        "children": [],
        "hosts": [
            "10.219.10.200",
            "10.219.185.101",
            "10.219.163.151",
            "10.219.150.33",
            "10.219.114.210",
            "10.219.75.150",
            "54.85.193.223",
            "54.84.199.152",
            "54.86.55.72",
            "54.86.76.239"
        ],
        "vars": {}
    },
    "tag_Stack_trial631": {
        "children": [],
        "hosts": [
            "10.219.53.235",
            "10.219.20.248",
            "10.219.27.228",
            "10.219.142.223",
            "10.219.68.180",
            "10.219.78.250",
            "54.86.97.174",
            "54.85.149.164",
            "54.85.207.233",
            "54.86.8.229"
        ],
        "vars": {}
    },
    "tag_Stack_trial632": {
        "children": [],
        "hosts": [
            "10.219.47.66",
            "10.219.52.205",
            "10.219.137.67",
            "10.219.185.140",
            "10.219.137.49",
            "10.219.110.47",
            "54.86.94.149",
            "54.86.88.52",
            "54.84.81.3",
            "54.86.93.172"
        ],
        "vars": {}
    },
    "tag_Stack_trial633": {
        "children": [],
        "hosts": [
            "10.219.13.250",
            "10.219.40.153",
            "10.219.5.136",
            "10.219.191.53",
            "10.219.119.27",
            "10.219.68.40",
            "54.86.98.67",
            "54.86.96.151",
            "54.86.99.19",
            "54.86.97.99"
        ],
        "vars": {}
    },
    "tag_Stack_trial634": {
        "children": [],
        "hosts": [
            "10.219.20.163",
            "10.219.11.33",
            "10.219.136.200",
            "10.219.183.41",
            "10.219.187.219",
            "10.219.97.127",
            "54.86.100.62",
            "54.85.11.117",
            "54.86.98.158",
            "54.86.99.25"
        ],
        "vars": {}
    },
    "tag_Stack_trial635": {
        "children": [],
        "hosts": [
            "10.219.5.238",
            "10.219.183.205",
            "10.219.134.176",
            "10.219.166.38",
            "10.219.127.169",
            "10.219.91.109",
            "54.86.112.96",
            "54.86.111.172",
            "54.86.111.175",
            "54.86.111.203"
        ],
        "vars": {}
    },
    "tag_Stack_trial636": {
        "children": [],
        "hosts": [
            "10.219.49.11",
            "10.219.138.5",
            "10.219.153.9",
            "10.219.165.155",
            "10.219.79.157",
            "10.219.121.158",
            "54.86.50.215",
            "54.85.248.82",
            "54.85.170.154",
            "54.85.148.231"
        ],
        "vars": {}
    },
    "tag_Stack_trial637": {
        "children": [],
        "hosts": [
            "10.219.32.235",
            "10.219.36.177",
            "10.219.159.21",
            "10.219.162.164",
            "10.219.167.0",
            "10.219.115.61",
            "54.86.112.106",
            "54.86.112.102",
            "54.86.3.216",
            "54.86.112.135"
        ],
        "vars": {}
    },
    "tag_Stack_trial638": {
        "children": [],
        "hosts": [
            "10.219.26.152",
            "10.219.6.136",
            "10.219.63.95",
            "10.219.130.129",
            "10.219.92.4",
            "10.219.68.254",
            "54.86.80.163",
            "54.86.78.119",
            "54.86.80.36",
            "54.86.80.208"
        ],
        "vars": {}
    },
    "tag_Stack_trial639": {
        "children": [],
        "hosts": [
            "10.219.3.22",
            "10.219.12.138",
            "10.219.18.43",
            "10.219.133.98",
            "10.219.179.156",
            "10.219.119.78",
            "54.86.87.183",
            "54.86.67.89",
            "54.86.104.169",
            "54.86.84.127"
        ],
        "vars": {}
    },
    "tag_Stack_trial640": {
        "children": [],
        "hosts": [
            "10.219.22.111",
            "10.219.28.211",
            "10.219.142.23",
            "10.219.165.247",
            "10.219.177.177",
            "10.219.78.180",
            "54.86.99.249",
            "54.86.90.71",
            "54.86.101.141",
            "54.86.94.238"
        ],
        "vars": {}
    },
    "tag_Stack_trial641": {
        "children": [],
        "hosts": [
            "10.219.10.83",
            "10.219.128.183",
            "10.219.158.35",
            "10.219.74.178",
            "10.219.71.164",
            "10.219.66.5",
            "54.84.167.146",
            "54.84.241.208",
            "54.86.61.31",
            "54.86.64.168"
        ],
        "vars": {}
    },
    "tag_Stack_trial642": {
        "children": [],
        "hosts": [
            "10.219.42.72",
            "10.219.49.157",
            "10.219.9.24",
            "10.219.131.26",
            "10.219.75.107",
            "10.219.77.162",
            "54.86.81.225",
            "54.86.65.171",
            "54.86.60.175",
            "54.86.81.213"
        ],
        "vars": {}
    },
    "tag_Stack_trial643": {
        "children": [],
        "hosts": [
            "10.219.30.9",
            "10.219.24.227",
            "10.219.175.97",
            "10.219.151.162",
            "10.219.132.1",
            "10.219.97.123",
            "54.86.79.232",
            "54.85.127.222",
            "54.86.45.250",
            "54.86.53.77"
        ],
        "vars": {}
    },
    "tag_Stack_trial644": {
        "children": [],
        "hosts": [
            "10.219.41.239",
            "10.219.32.15",
            "10.219.175.162",
            "10.219.64.58",
            "10.219.124.145",
            "10.219.125.7",
            "54.86.106.242",
            "54.86.106.241",
            "54.86.106.244",
            "54.86.106.243"
        ],
        "vars": {}
    },
    "tag_Stack_trial645": {
        "children": [],
        "hosts": [
            "10.219.31.244",
            "10.219.143.239",
            "10.219.140.250",
            "10.219.147.25",
            "10.219.93.219",
            "10.219.101.155",
            "54.86.98.77",
            "54.86.98.21",
            "54.86.38.49",
            "54.85.98.144"
        ],
        "vars": {}
    },
    "tag_Stack_trial646": {
        "children": [],
        "hosts": [
            "10.219.50.231",
            "10.219.18.88",
            "10.219.62.182",
            "10.219.135.107",
            "10.219.168.254",
            "10.219.89.22",
            "54.86.85.33",
            "54.85.77.167",
            "54.85.251.175",
            "54.86.80.182"
        ],
        "vars": {}
    },
    "tag_Stack_trial647": {
        "children": [],
        "hosts": [
            "10.219.9.54",
            "10.219.61.3",
            "10.219.156.2",
            "10.219.102.143",
            "10.219.87.56",
            "10.219.67.205",
            "54.86.108.101",
            "54.86.108.102",
            "54.86.108.119",
            "54.86.108.117"
        ],
        "vars": {}
    },
    "tag_Stack_white-ops": {
        "children": [],
        "hosts": [
            "10.219.6.165",
            "10.219.16.100",
            "10.219.43.249",
            "10.219.157.181",
            "10.219.127.168",
            "10.219.90.31",
            "54.84.148.213",
            "54.84.149.162",
            "54.84.15.178",
            "54.208.10.193"
        ],
        "vars": {}
    },
    "tag_Stack_zabbix": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-182": {
        "children": [],
        "hosts": [
            "10.219.5.111",
            "10.219.63.105",
            "10.219.137.105",
            "10.219.168.41",
            "10.219.131.132",
            "10.219.91.234",
            "54.85.54.254",
            "54.85.181.37",
            "54.85.76.42",
            "54.85.68.39"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-194": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-251": {
        "children": [],
        "hosts": [
            "10.219.18.251",
            "10.219.183.156",
            "10.219.174.165",
            "10.219.154.184",
            "10.219.84.105",
            "10.219.107.166",
            "54.84.217.136",
            "54.84.116.38",
            "54.84.97.29",
            "54.85.42.39"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-279": {
        "children": [],
        "hosts": [
            "10.219.40.115",
            "10.219.49.237",
            "10.219.188.5",
            "10.219.112.202",
            "10.219.103.26",
            "10.219.81.130",
            "54.85.10.98",
            "54.85.16.252",
            "54.84.228.141",
            "54.85.65.51"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-296": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "10.219.47.252",
            "10.219.53.81",
            "10.219.134.206",
            "10.219.86.78",
            "10.219.92.102",
            "54.84.92.185",
            "54.84.84.233",
            "54.84.87.73",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-303": {
        "children": [],
        "hosts": [
            "10.219.31.47",
            "10.219.128.227",
            "10.219.173.45",
            "10.219.107.101",
            "10.219.91.14",
            "10.219.65.35",
            "54.84.207.241",
            "54.85.34.98",
            "54.84.245.20",
            "54.84.191.190"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-330": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "10.219.52.143",
            "10.219.173.93",
            "10.219.145.78",
            "10.219.98.174",
            "10.219.127.143",
            "10.219.68.240",
            "54.84.152.213",
            "54.84.156.145",
            "54.84.122.210",
            "54.84.189.190",
            "54.84.80.225",
            "54.84.189.117"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-35": {
        "children": [],
        "hosts": [
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-351": {
        "children": [],
        "hosts": [
            "10.219.6.165",
            "10.219.16.100",
            "10.219.43.249",
            "10.219.157.181",
            "10.219.127.168",
            "10.219.90.31",
            "54.84.148.213",
            "54.84.149.162",
            "54.84.15.178",
            "54.208.10.193"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-358": {
        "children": [],
        "hosts": [
            "10.219.1.9",
            "10.219.4.181",
            "10.219.147.195",
            "10.219.132.7",
            "10.219.171.92",
            "10.219.68.99",
            "54.84.99.227",
            "54.84.164.51",
            "54.84.155.209",
            "54.84.142.102"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-398": {
        "children": [],
        "hosts": [
            "10.219.11.12",
            "10.219.136.66",
            "10.219.136.17",
            "10.219.179.164",
            "10.219.98.192",
            "10.219.105.247",
            "54.84.125.108",
            "54.84.199.223",
            "54.84.164.99",
            "54.84.222.7",
            "54.84.206.192",
            "54.84.185.247"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-436": {
        "children": [],
        "hosts": [
            "10.219.28.78",
            "10.219.190.234",
            "10.219.186.145",
            "10.219.168.89",
            "10.219.127.193",
            "10.219.113.16",
            "54.85.13.176",
            "54.84.137.179",
            "54.84.242.116",
            "54.84.222.25"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-478": {
        "children": [],
        "hosts": [
            "10.219.32.233",
            "10.219.16.141",
            "10.219.25.43",
            "10.219.131.134",
            "10.219.146.30",
            "10.219.189.153",
            "10.219.182.240",
            "10.219.181.82",
            "10.219.118.63",
            "10.219.81.15",
            "10.219.85.37",
            "10.219.100.34",
            "54.85.53.103",
            "54.85.33.186",
            "54.85.32.12",
            "54.85.66.59",
            "54.85.52.64",
            "54.85.21.183",
            "54.85.28.140",
            "54.84.252.121"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-493": {
        "children": [],
        "hosts": [
            "10.219.48.166",
            "10.219.49.54",
            "10.219.166.184",
            "10.219.85.245",
            "10.219.107.232",
            "10.219.126.78",
            "54.84.84.30",
            "54.85.71.17",
            "54.84.166.253",
            "54.85.71.54"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-494": {
        "children": [],
        "hosts": [
            "10.219.43.57",
            "10.219.12.85",
            "10.219.137.198",
            "10.219.150.111",
            "10.219.177.243",
            "10.219.72.93",
            "54.85.69.157",
            "54.85.69.123",
            "54.85.45.216",
            "54.84.170.133"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-495": {
        "children": [],
        "hosts": [
            "10.219.47.1",
            "10.219.63.147",
            "10.219.130.240",
            "10.219.169.253",
            "10.219.130.190",
            "10.219.125.232",
            "54.84.23.79",
            "54.85.80.174",
            "54.86.39.175",
            "54.85.72.146",
            "54.84.47.238",
            "54.84.74.125"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-546": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-549": {
        "children": [],
        "hosts": [
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.120.23",
            "10.219.118.52",
            "10.219.177.150",
            "10.219.144.224",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.16.214",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-562": {
        "children": [],
        "hosts": [
            "10.219.60.213",
            "10.219.153.220",
            "10.219.154.94",
            "10.219.130.229",
            "10.219.72.134",
            "10.219.94.77",
            "54.84.46.105",
            "54.85.91.87",
            "54.84.190.109",
            "54.85.148.101"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-635": {
        "children": [],
        "hosts": [
            "10.219.39.9",
            "10.219.26.28",
            "10.219.60.102",
            "10.219.178.85",
            "10.219.108.141",
            "10.219.81.29",
            "54.86.57.201",
            "54.85.14.238",
            "54.85.75.200",
            "54.86.40.17"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-636": {
        "children": [],
        "hosts": [
            "10.219.11.70",
            "10.219.5.147",
            "10.219.16.66",
            "10.219.158.176",
            "10.219.142.79",
            "10.219.100.175",
            "54.85.87.129",
            "54.84.163.82",
            "54.208.228.127",
            "54.84.251.0"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-637": {
        "children": [],
        "hosts": [
            "10.219.62.192",
            "10.219.41.67",
            "10.219.18.78",
            "10.219.185.71",
            "10.219.147.74",
            "10.219.98.173",
            "54.86.90.15",
            "54.86.90.142",
            "54.86.90.152",
            "54.86.90.177"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-638": {
        "children": [],
        "hosts": [
            "54.85.161.87",
            "54.85.90.7",
            "54.208.59.237",
            "54.85.199.140"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-639": {
        "children": [],
        "hosts": [
            "10.219.17.208",
            "10.219.185.186",
            "10.219.154.115",
            "10.219.155.180",
            "10.219.103.150",
            "10.219.67.120",
            "54.208.141.20",
            "54.209.120.55",
            "54.208.210.176",
            "54.209.108.61"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-640": {
        "children": [],
        "hosts": [
            "54.84.169.33",
            "54.209.106.125",
            "54.84.240.188",
            "54.84.192.78"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-641": {
        "children": [],
        "hosts": [
            "10.219.56.242",
            "10.219.30.68",
            "10.219.57.108",
            "10.219.133.48",
            "10.219.89.90",
            "10.219.111.113",
            "54.84.21.94",
            "54.85.48.128",
            "54.85.208.32",
            "54.85.27.197"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-642": {
        "children": [],
        "hosts": [
            "10.219.36.102",
            "10.219.11.190",
            "10.219.140.138",
            "10.219.178.84",
            "10.219.155.123",
            "10.219.90.205",
            "54.85.53.185",
            "54.86.75.36",
            "54.84.114.2",
            "54.86.76.41"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-643": {
        "children": [],
        "hosts": [
            "10.219.16.89",
            "10.219.149.40",
            "10.219.142.242",
            "10.219.114.207",
            "10.219.79.196",
            "10.219.85.43",
            "54.86.102.132",
            "54.86.110.180",
            "54.86.110.115",
            "54.86.52.195"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-644": {
        "children": [],
        "hosts": [
            "10.219.18.12",
            "10.219.19.226",
            "10.219.180.178",
            "10.219.81.201",
            "10.219.94.27",
            "10.219.117.252",
            "54.86.103.5",
            "54.86.105.40",
            "54.86.104.18",
            "54.86.94.75"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-645": {
        "children": [],
        "hosts": [
            "10.219.15.194",
            "10.219.12.146",
            "10.219.138.98",
            "10.219.145.106",
            "10.219.137.205",
            "10.219.86.47",
            "54.85.200.49",
            "54.208.45.55",
            "54.85.95.0",
            "54.85.119.67"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-646": {
        "children": [],
        "hosts": [
            "10.219.2.224",
            "10.219.48.124",
            "10.219.154.12",
            "10.219.92.64",
            "10.219.85.31",
            "10.219.89.30",
            "54.209.204.12",
            "54.85.223.164",
            "54.209.14.115",
            "54.209.203.222"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-647": {
        "children": [],
        "hosts": [
            "10.219.14.143",
            "10.219.4.55",
            "10.219.130.1",
            "10.219.169.68",
            "10.219.180.244",
            "10.219.122.228",
            "54.84.54.49",
            "54.85.166.231",
            "54.84.245.162",
            "54.85.249.26"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-648": {
        "children": [],
        "hosts": [
            "10.219.60.118",
            "10.219.41.191",
            "10.219.41.230",
            "10.219.147.63",
            "10.219.173.37",
            "10.219.64.87",
            "54.86.53.153",
            "54.86.74.37",
            "54.86.81.21",
            "54.86.89.186"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-649": {
        "children": [],
        "hosts": [
            "10.219.56.83",
            "10.219.36.162",
            "10.219.45.70",
            "10.219.177.41",
            "10.219.154.211",
            "10.219.96.145",
            "54.86.117.161",
            "54.86.117.163",
            "54.86.117.162",
            "54.86.111.80"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-650": {
        "children": [],
        "hosts": [
            "10.219.48.23",
            "10.219.54.28",
            "10.219.143.130",
            "10.219.109.92",
            "10.219.121.80",
            "10.219.109.28",
            "54.85.135.14",
            "54.208.12.112",
            "54.84.103.10",
            "54.209.76.22"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-651": {
        "children": [],
        "hosts": [
            "10.219.47.118",
            "10.219.143.228",
            "10.219.187.178",
            "10.219.154.203",
            "10.219.88.75",
            "10.219.97.207",
            "54.209.74.106",
            "54.85.85.59",
            "54.85.48.70",
            "54.208.187.98"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-652": {
        "children": [],
        "hosts": [
            "10.219.43.2",
            "10.219.39.144",
            "10.219.63.67",
            "10.219.184.234",
            "10.219.163.166",
            "10.219.68.47",
            "54.209.127.172",
            "54.85.84.167",
            "54.85.47.154",
            "54.209.108.176"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-653": {
        "children": [],
        "hosts": [
            "10.219.39.139",
            "10.219.37.47",
            "10.219.25.26",
            "10.219.136.13",
            "10.219.146.42",
            "10.219.78.42",
            "54.85.61.212",
            "54.84.190.144",
            "54.85.255.219",
            "54.85.173.90"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-654": {
        "children": [],
        "hosts": [
            "54.84.174.209",
            "54.85.44.185",
            "54.208.89.118",
            "54.85.160.181"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-655": {
        "children": [],
        "hosts": [
            "10.219.36.26",
            "10.219.37.213",
            "10.219.142.152",
            "10.219.169.135",
            "10.219.138.185",
            "10.219.111.126",
            "54.86.117.236",
            "54.86.117.237",
            "54.86.116.105",
            "54.86.116.199"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-666": {
        "children": [],
        "hosts": [
            "10.219.29.108",
            "10.219.3.208",
            "10.219.56.12",
            "10.219.184.152",
            "10.219.93.172",
            "10.219.103.216",
            "54.85.42.61",
            "54.208.87.90",
            "54.85.102.208",
            "54.209.139.239"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-682": {
        "children": [],
        "hosts": [
            "10.219.8.78",
            "10.219.59.221",
            "10.219.38.61",
            "10.219.62.128",
            "10.219.167.28",
            "10.219.165.216",
            "10.219.156.153",
            "10.219.67.44",
            "10.219.82.113",
            "54.209.162.114",
            "54.209.183.210",
            "54.85.80.156",
            "54.84.31.76",
            "54.85.52.37",
            "54.85.47.190",
            "54.209.177.56"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-739": {
        "children": [],
        "hosts": [
            "10.219.17.109",
            "10.219.51.115",
            "10.219.55.210",
            "10.219.41.127",
            "10.219.4.113",
            "10.219.189.219",
            "10.219.152.17",
            "10.219.169.240",
            "10.219.112.253",
            "10.219.64.207",
            "10.219.97.164",
            "10.219.118.126",
            "54.86.85.22",
            "54.84.193.141",
            "54.84.18.13",
            "54.85.193.109",
            "54.86.84.64",
            "54.85.167.62",
            "54.85.126.177",
            "54.86.75.79",
            "54.86.14.157",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-749": {
        "children": [],
        "hosts": [
            "10.219.59.159",
            "10.219.24.179",
            "10.219.9.203",
            "10.219.173.38",
            "10.219.77.13",
            "10.219.66.9",
            "54.86.71.155",
            "54.86.82.149",
            "54.86.77.91",
            "54.86.87.25"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-750": {
        "children": [],
        "hosts": [
            "10.219.53.83",
            "10.219.25.150",
            "10.219.128.18",
            "10.219.119.127",
            "10.219.118.148",
            "10.219.109.144",
            "54.86.97.227",
            "54.85.75.4",
            "54.86.97.181",
            "54.86.97.144"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-751": {
        "children": [],
        "hosts": [
            "10.219.27.75",
            "10.219.129.154",
            "10.219.155.112",
            "10.219.123.229",
            "10.219.73.211",
            "10.219.114.130",
            "54.86.90.204",
            "54.86.78.51",
            "54.86.92.153",
            "54.86.91.120"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-752": {
        "children": [],
        "hosts": [
            "10.219.2.72",
            "10.219.32.78",
            "10.219.63.214",
            "10.219.161.92",
            "10.219.152.253",
            "10.219.75.209",
            "54.86.97.67",
            "54.86.97.73",
            "54.85.196.193",
            "54.86.60.192"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-753": {
        "children": [],
        "hosts": [
            "10.219.10.200",
            "10.219.185.101",
            "10.219.163.151",
            "10.219.150.33",
            "10.219.114.210",
            "10.219.75.150",
            "54.85.193.223",
            "54.84.199.152",
            "54.86.55.72",
            "54.86.76.239"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-754": {
        "children": [],
        "hosts": [
            "10.219.53.235",
            "10.219.20.248",
            "10.219.27.228",
            "10.219.142.223",
            "10.219.68.180",
            "10.219.78.250",
            "54.86.97.174",
            "54.85.149.164",
            "54.85.207.233",
            "54.86.8.229"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-755": {
        "children": [],
        "hosts": [
            "10.219.47.66",
            "10.219.52.205",
            "10.219.137.67",
            "10.219.185.140",
            "10.219.137.49",
            "10.219.110.47",
            "54.86.94.149",
            "54.86.88.52",
            "54.84.81.3",
            "54.86.93.172"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-756": {
        "children": [],
        "hosts": [
            "10.219.13.250",
            "10.219.40.153",
            "10.219.5.136",
            "10.219.191.53",
            "10.219.119.27",
            "10.219.68.40",
            "54.86.98.67",
            "54.86.96.151",
            "54.86.99.19",
            "54.86.97.99"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-757": {
        "children": [],
        "hosts": [
            "10.219.20.163",
            "10.219.11.33",
            "10.219.136.200",
            "10.219.183.41",
            "10.219.187.219",
            "10.219.97.127",
            "54.86.100.62",
            "54.85.11.117",
            "54.86.98.158",
            "54.86.99.25"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-758": {
        "children": [],
        "hosts": [
            "10.219.5.238",
            "10.219.183.205",
            "10.219.134.176",
            "10.219.166.38",
            "10.219.127.169",
            "10.219.91.109",
            "54.86.112.96",
            "54.86.111.172",
            "54.86.111.175",
            "54.86.111.203"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-759": {
        "children": [],
        "hosts": [
            "10.219.49.11",
            "10.219.138.5",
            "10.219.153.9",
            "10.219.165.155",
            "10.219.79.157",
            "10.219.121.158",
            "54.86.50.215",
            "54.85.248.82",
            "54.85.170.154",
            "54.85.148.231"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-760": {
        "children": [],
        "hosts": [
            "10.219.32.235",
            "10.219.36.177",
            "10.219.159.21",
            "10.219.162.164",
            "10.219.167.0",
            "10.219.115.61",
            "54.86.112.106",
            "54.86.112.102",
            "54.86.3.216",
            "54.86.112.135"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-807": {
        "children": [],
        "hosts": [
            "10.219.35.86",
            "10.219.9.213",
            "10.219.141.55",
            "10.219.134.179",
            "10.219.155.57",
            "10.219.83.87",
            "54.84.156.195",
            "54.86.54.174",
            "54.85.37.235",
            "54.85.175.102"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-810": {
        "children": [],
        "hosts": [
            "10.219.56.91",
            "10.219.56.44",
            "10.219.36.235",
            "10.219.39.194",
            "10.219.154.60",
            "10.219.175.103",
            "10.219.150.186",
            "10.219.84.189",
            "10.219.71.223",
            "54.86.48.214",
            "54.86.80.199",
            "54.86.10.255",
            "54.86.56.174",
            "54.86.89.139",
            "54.86.81.117",
            "54.86.88.208"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-813": {
        "children": [],
        "hosts": [
            "10.219.26.152",
            "10.219.6.136",
            "10.219.63.95",
            "10.219.130.129",
            "10.219.92.4",
            "10.219.68.254",
            "54.86.80.163",
            "54.86.78.119",
            "54.86.80.36",
            "54.86.80.208"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-814": {
        "children": [],
        "hosts": [
            "10.219.3.22",
            "10.219.12.138",
            "10.219.18.43",
            "10.219.133.98",
            "10.219.179.156",
            "10.219.119.78",
            "54.86.87.183",
            "54.86.67.89",
            "54.86.104.169",
            "54.86.84.127"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-815": {
        "children": [],
        "hosts": [
            "10.219.22.111",
            "10.219.28.211",
            "10.219.142.23",
            "10.219.165.247",
            "10.219.177.177",
            "10.219.78.180",
            "54.86.99.249",
            "54.86.90.71",
            "54.86.101.141",
            "54.86.94.238"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-816": {
        "children": [],
        "hosts": [
            "10.219.10.83",
            "10.219.128.183",
            "10.219.158.35",
            "10.219.74.178",
            "10.219.71.164",
            "10.219.66.5",
            "54.84.167.146",
            "54.84.241.208",
            "54.86.61.31",
            "54.86.64.168"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-817": {
        "children": [],
        "hosts": [
            "10.219.42.72",
            "10.219.49.157",
            "10.219.9.24",
            "10.219.131.26",
            "10.219.75.107",
            "10.219.77.162",
            "54.86.81.225",
            "54.86.65.171",
            "54.86.60.175",
            "54.86.81.213"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-818": {
        "children": [],
        "hosts": [
            "10.219.30.9",
            "10.219.24.227",
            "10.219.175.97",
            "10.219.151.162",
            "10.219.132.1",
            "10.219.97.123",
            "54.86.79.232",
            "54.85.127.222",
            "54.86.45.250",
            "54.86.53.77"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-819": {
        "children": [],
        "hosts": [
            "10.219.41.239",
            "10.219.32.15",
            "10.219.175.162",
            "10.219.64.58",
            "10.219.124.145",
            "10.219.125.7",
            "54.86.106.242",
            "54.86.106.241",
            "54.86.106.244",
            "54.86.106.243"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-820": {
        "children": [],
        "hosts": [
            "10.219.31.244",
            "10.219.143.239",
            "10.219.140.250",
            "10.219.147.25",
            "10.219.93.219",
            "10.219.101.155",
            "54.86.98.77",
            "54.86.98.21",
            "54.86.38.49",
            "54.85.98.144"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-821": {
        "children": [],
        "hosts": [
            "10.219.50.231",
            "10.219.18.88",
            "10.219.62.182",
            "10.219.135.107",
            "10.219.168.254",
            "10.219.89.22",
            "54.86.85.33",
            "54.85.77.167",
            "54.85.251.175",
            "54.86.80.182"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-822": {
        "children": [],
        "hosts": [
            "10.219.9.54",
            "10.219.61.3",
            "10.219.156.2",
            "10.219.102.143",
            "10.219.87.56",
            "10.219.67.205",
            "54.86.108.101",
            "54.86.108.102",
            "54.86.108.119",
            "54.86.108.117"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-853": {
        "children": [],
        "hosts": [
            "10.219.51.0",
            "10.219.165.236",
            "10.219.136.115",
            "10.219.72.12",
            "10.219.69.7",
            "10.219.101.208",
            "54.86.119.45",
            "54.86.109.129",
            "54.86.109.121",
            "54.86.112.246"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-854": {
        "children": [],
        "hosts": [
            "10.219.1.219",
            "10.219.49.160",
            "10.219.184.95",
            "10.219.92.107",
            "10.219.117.146",
            "10.219.70.210",
            "54.86.107.51",
            "54.86.125.136",
            "54.86.94.44",
            "54.86.128.114"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-865": {
        "children": [],
        "hosts": [
            "10.219.43.48",
            "10.219.132.76",
            "10.219.147.27",
            "10.219.95.221",
            "10.219.64.89",
            "10.219.85.120",
            "54.86.141.183",
            "54.86.141.184",
            "54.86.141.187",
            "54.86.103.185"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-874": {
        "children": [],
        "hosts": [
            "10.219.129.226",
            "54.86.101.162"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-895": {
        "children": [],
        "hosts": [
            "10.219.152.142"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-915": {
        "children": [],
        "hosts": [
            "10.219.29.254",
            "10.219.25.147",
            "10.219.161.118",
            "10.219.152.52",
            "10.219.188.151",
            "10.219.114.174"
        ],
        "vars": {}
    },
    "tag_Ticket_CO-920": {
        "children": [],
        "hosts": [
            "10.219.62.215",
            "10.219.45.160",
            "10.219.10.116",
            "10.219.164.5",
            "10.219.147.76",
            "10.219.87.108"
        ],
        "vars": {}
    },
    "tag_customer_type_Customer": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.84.245.20",
            "54.84.149.162",
            "54.84.189.190",
            "54.84.122.210",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.84.148.213",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.10.98",
            "54.85.54.254",
            "54.84.46.105",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.107.101",
            "10.219.112.202",
            "10.219.157.181",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.183.156",
            "10.219.131.132",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.136.115",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.152.142",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.60.213",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.83.87",
            "10.219.174.165",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.9.213",
            "10.219.35.86"
        ],
        "vars": {}
    },
    "tag_customer_type_Dev": {
        "children": [],
        "hosts": [
            "10.219.62.215",
            "10.219.45.160",
            "10.219.10.116",
            "10.219.43.57",
            "10.219.47.1",
            "10.219.63.147",
            "10.219.12.85",
            "10.219.130.240",
            "10.219.169.253",
            "10.219.130.190",
            "10.219.137.198",
            "10.219.150.111",
            "10.219.177.243",
            "10.219.125.232",
            "10.219.72.93",
            "10.219.164.5",
            "10.219.147.76",
            "10.219.87.108"
        ],
        "vars": {}
    },
    "tag_customer_type_Ops": {
        "children": [],
        "hosts": [
            "10.219.43.120",
            "54.84.42.12"
        ],
        "vars": {}
    },
    "tag_customer_type_POC": {
        "children": [],
        "hosts": [
            "54.84.65.195",
            "54.84.87.73",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.252.121",
            "54.85.28.140",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.84.233",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.89.139",
            "54.86.56.174",
            "54.84.92.185",
            "54.84.99.227",
            "54.84.125.108",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.85.69.157",
            "10.219.92.102",
            "10.219.86.78",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.90.205",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.134.206",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.174.165",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.61.154",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.43.57",
            "10.219.114.174",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.25.147",
            "10.219.29.254"
        ],
        "vars": {}
    },
    "tag_customer_type_Test": {
        "children": [],
        "hosts": [
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.120.23",
            "10.219.118.52",
            "10.219.177.150",
            "10.219.144.224",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.16.214",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "tag_customer_type_Trial": {
        "children": [],
        "hosts": [
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.77.91",
            "54.86.99.19",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.90.205",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.136.13",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.17.208",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.25.26",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11"
        ],
        "vars": {}
    },
    "tag_customer_type_dev": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_stack_version_SR_8_HF1": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_stackmakr_version_9109": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_stackmakr_version_SEC-1553-20140326T1633-SR_8_HF1": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.84.65.195",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.28.140",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.189.190",
            "54.84.122.210",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.75.99",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.84.92.185",
            "54.84.148.213",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.86.23.145",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.92.102",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.92.169",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.115.77",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.107.101",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.112.202",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.118.52",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.131.132",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.136.115",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.132.135",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.144.224",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.152.142",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.61.154",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.12.148",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.25.147",
            "10.219.29.254",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "tag_whisper_version_99": {
        "children": [],
        "hosts": [
            "10.219.41.51",
            "10.219.59.57",
            "10.219.26.121",
            "10.219.179.119",
            "10.219.160.142",
            "10.219.119.218"
        ],
        "vars": {}
    },
    "tag_whisper_version_SEC-1318-20130212T1441-WR_16_HF2": {
        "children": [],
        "hosts": [
            "10.219.61.154",
            "10.219.47.252",
            "10.219.53.81",
            "10.219.134.206",
            "10.219.86.78",
            "10.219.92.102",
            "54.84.92.185",
            "54.84.84.233",
            "54.84.87.73",
            "54.84.65.195"
        ],
        "vars": {}
    },
    "tag_whisper_version_SEC-1518-20140319T1154-WR_17_HF2": {
        "children": [],
        "hosts": [
            "54.208.10.193",
            "54.84.15.178",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.28.140",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.84.75.99",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.84.148.213",
            "54.84.99.227",
            "54.84.125.108",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.86.23.145",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.85.69.157",
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.92.169",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.115.77",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.107.101",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.112.202",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.118.52",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.157.181",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.131.132",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.132.135",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.144.224",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.12.148",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.16.214",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "tag_whisper_version_SEC-1639-20140414T1539-WR_17_HF3": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.84.189.117",
            "54.84.80.225",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.189.190",
            "54.84.122.210",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.136.115",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.152.142",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.25.147",
            "10.219.29.254",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215"
        ],
        "vars": {}
    },
    "tag_whisper_version____SEC-1639-20140414T1539-WR_17_HF3": {
        "children": [],
        "hosts": [
            "10.219.55.210",
            "10.219.41.127",
            "10.219.4.113",
            "10.219.169.240",
            "10.219.97.164",
            "10.219.118.126",
            "54.84.18.13",
            "54.85.193.109",
            "54.85.126.177",
            "54.84.0.249"
        ],
        "vars": {}
    },
    "type_c1_medium": {
        "children": [],
        "hosts": [
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "type_c3_2xlarge": {
        "children": [],
        "hosts": [
            "54.86.141.187",
            "54.84.65.195",
            "54.85.28.140",
            "54.84.166.253",
            "54.85.65.51",
            "54.84.245.20",
            "54.84.240.188",
            "54.209.76.22",
            "54.208.89.118",
            "54.209.14.115",
            "54.86.52.195",
            "54.86.94.75",
            "54.86.91.120",
            "54.86.97.144",
            "54.86.61.31",
            "54.86.106.244",
            "54.86.108.117",
            "54.84.164.51",
            "54.84.97.29",
            "54.85.52.64",
            "54.85.69.123",
            "54.85.72.146",
            "54.84.190.109",
            "54.208.210.176",
            "54.208.45.55",
            "54.85.48.70",
            "54.84.245.162",
            "54.84.114.2",
            "54.85.170.154",
            "54.86.116.105",
            "54.86.55.72",
            "54.86.88.52",
            "54.86.98.158",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.101.141",
            "54.86.45.250",
            "54.86.98.21",
            "54.85.90.7",
            "54.208.87.90",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.87.129",
            "54.84.21.94",
            "54.86.57.201",
            "54.86.74.37",
            "54.86.117.161",
            "54.86.71.155",
            "54.86.97.67",
            "54.86.97.174",
            "54.86.98.67",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.65.171",
            "54.86.67.89",
            "54.86.85.33",
            "10.219.95.221",
            "10.219.92.102",
            "10.219.85.37",
            "10.219.85.245",
            "10.219.81.130",
            "10.219.107.101",
            "10.219.109.28",
            "10.219.85.31",
            "10.219.79.196",
            "10.219.117.252",
            "10.219.114.130",
            "10.219.109.144",
            "10.219.74.178",
            "10.219.64.58",
            "10.219.67.205",
            "10.219.147.195",
            "10.219.154.184",
            "10.219.182.240",
            "10.219.150.111",
            "10.219.169.253",
            "10.219.154.94",
            "10.219.154.115",
            "10.219.138.98",
            "10.219.154.203",
            "10.219.169.68",
            "10.219.155.123",
            "10.219.153.9",
            "10.219.138.185",
            "10.219.163.151",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.134.176",
            "10.219.159.21",
            "10.219.177.177",
            "10.219.132.1",
            "10.219.143.239",
            "10.219.154.235",
            "10.219.56.12",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.5.147",
            "10.219.56.242",
            "10.219.39.9",
            "10.219.41.230",
            "10.219.56.83",
            "10.219.59.159",
            "10.219.2.72",
            "10.219.53.235",
            "10.219.13.250",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.49.157",
            "10.219.18.43",
            "10.219.50.231",
            "10.219.161.188",
            "10.219.161.118",
            "10.219.10.116",
            "10.219.152.208",
            "10.219.167.181"
        ],
        "vars": {}
    },
    "type_c3_4xlarge": {
        "children": [],
        "hosts": [
            "10.219.56.44",
            "10.219.12.148",
            "10.219.132.135",
            "10.219.131.132",
            "10.219.92.169",
            "54.86.80.199",
            "54.85.76.42"
        ],
        "vars": {}
    },
    "type_c3_8xlarge": {
        "children": [],
        "hosts": [
            "10.219.4.79",
            "10.219.68.240",
            "54.84.152.213"
        ],
        "vars": {}
    },
    "type_hs1_8xlarge": {
        "children": [],
        "hosts": [
            "54.86.128.114",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.0.249",
            "54.86.14.157",
            "54.86.75.79",
            "54.84.189.190",
            "54.85.126.177",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.125.136",
            "54.84.180.204",
            "54.84.103.231",
            "54.84.18.13",
            "54.84.193.141",
            "54.86.85.22",
            "54.86.107.51",
            "10.219.70.210",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.118.126",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.145.78",
            "10.219.169.240",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.184.95",
            "10.219.62.184",
            "10.219.36.226",
            "10.219.55.210",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.1.219"
        ],
        "vars": {}
    },
    "type_m1_large": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com",
            "ec2-50-19-44-148.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "54.84.206.192",
            "54.84.222.7",
            "54.84.122.210",
            "54.86.39.175",
            "54.86.101.162",
            "54.208.96.71",
            "54.84.156.145",
            "54.84.23.79",
            "10.219.72.12",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.100.237",
            "10.219.115.245",
            "10.219.98.192",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.118.63",
            "10.219.107.232",
            "10.219.94.77",
            "10.219.115.77",
            "10.219.103.150",
            "10.219.93.172",
            "10.219.121.80",
            "10.219.97.207",
            "10.219.92.64",
            "10.219.111.113",
            "10.219.112.202",
            "10.219.97.164",
            "10.219.108.141",
            "10.219.118.52",
            "10.219.79.157",
            "10.219.85.43",
            "10.219.66.9",
            "10.219.81.201",
            "10.219.123.229",
            "10.219.75.150",
            "10.219.68.180",
            "10.219.119.127",
            "10.219.119.27",
            "10.219.127.169",
            "10.219.68.254",
            "10.219.77.162",
            "10.219.71.164",
            "10.219.124.145",
            "10.219.87.56",
            "10.219.101.155",
            "10.219.171.92",
            "10.219.179.164",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.190.234",
            "10.219.128.227",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.146.30",
            "10.219.137.198",
            "10.219.130.240",
            "10.219.160.142",
            "10.219.130.229",
            "10.219.137.105",
            "10.219.136.115",
            "10.219.155.180",
            "10.219.137.205",
            "10.219.143.228",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.180.244",
            "10.219.158.176",
            "10.219.165.216",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.134.179",
            "10.219.173.37",
            "10.219.142.242",
            "10.219.154.211",
            "10.219.169.135",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.187.219",
            "10.219.137.67",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.183.205",
            "10.219.165.247",
            "10.219.128.183",
            "10.219.151.162",
            "10.219.133.98",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.154.60",
            "10.219.164.210",
            "10.219.161.181",
            "10.219.144.224",
            "10.219.132.76",
            "10.219.129.226",
            "10.219.142.198",
            "10.219.177.248",
            "10.219.14.89",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.26.182",
            "10.219.33.86",
            "10.219.57.225",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.1.9",
            "10.219.52.143",
            "10.219.16.141",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.47.1",
            "10.219.26.121",
            "10.219.41.51",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.15.194",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.4.55",
            "10.219.11.70",
            "10.219.30.68",
            "10.219.59.221",
            "10.219.41.127",
            "10.219.26.28",
            "10.219.36.102",
            "10.219.9.213",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.9.203",
            "10.219.19.226",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.27.228",
            "10.219.25.150",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.52.205",
            "10.219.36.177",
            "10.219.41.67",
            "10.219.6.136",
            "10.219.28.211",
            "10.219.9.24",
            "10.219.12.138",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.39.194",
            "10.219.49.160",
            "10.219.91.91",
            "10.219.164.5",
            "10.219.134.89",
            "10.219.152.52",
            "10.219.29.254",
            "10.219.45.160",
            "10.219.111.100",
            "10.219.132.127",
            "10.219.111.13",
            "10.219.166.102"
        ],
        "vars": {}
    },
    "type_m1_medium": {
        "children": [],
        "hosts": [
            "10.219.50.248",
            "54.84.149.25",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "type_m1_small": {
        "children": [],
        "hosts": [
            "10.219.23.181",
            "10.219.164.166",
            "10.219.123.163",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "54.208.124.14",
            "54.84.37.150",
            "54.84.41.152",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com"
        ],
        "vars": {}
    },
    "type_m1_xlarge": {
        "children": [],
        "hosts": [
            "54.86.103.185",
            "54.84.142.102",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.192.78",
            "54.85.119.67",
            "54.209.139.239",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.209.203.222",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.80.182",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.155.209",
            "54.85.34.98",
            "54.84.116.38",
            "54.85.66.59",
            "54.85.71.17",
            "54.85.45.216",
            "54.84.47.238",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.208.59.237",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.75.200",
            "54.86.75.36",
            "54.85.248.82",
            "54.86.77.91",
            "54.86.99.19",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.141.184",
            "54.84.42.12",
            "54.84.99.227",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.84.84.30",
            "54.85.80.174",
            "54.85.10.98",
            "54.85.54.254",
            "54.84.46.105",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.48.128",
            "54.85.14.238",
            "54.85.53.185",
            "54.86.50.215",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.81.225",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.10.255",
            "54.86.48.214",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.64.89",
            "10.219.64.217",
            "10.219.78.69",
            "10.219.68.99",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.81.15",
            "10.219.126.78",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.119.218",
            "10.219.72.134",
            "10.219.67.120",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.89.90",
            "10.219.81.29",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.121.158",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.77.13",
            "10.219.73.211",
            "10.219.75.209",
            "10.219.78.250",
            "10.219.114.210",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.68.40",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.98.173",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.89.22",
            "10.219.102.143",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.132.7",
            "10.219.173.45",
            "10.219.174.165",
            "10.219.189.153",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.130.190",
            "10.219.179.119",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.188.5",
            "10.219.185.186",
            "10.219.145.106",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.163.166",
            "10.219.154.12",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.133.48",
            "10.219.177.150",
            "10.219.178.85",
            "10.219.178.84",
            "10.219.138.5",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.147.63",
            "10.219.149.40",
            "10.219.177.41",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.137.49",
            "10.219.128.18",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.179.156",
            "10.219.175.97",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.147.27",
            "10.219.182.219",
            "10.219.43.120",
            "10.219.4.181",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.49.54",
            "10.219.63.147",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.59.57",
            "10.219.60.213",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.3.208",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.2.224",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.57.108",
            "10.219.60.102",
            "10.219.11.190",
            "10.219.49.11",
            "10.219.41.191",
            "10.219.36.162",
            "10.219.16.89",
            "10.219.37.213",
            "10.219.24.179",
            "10.219.18.12",
            "10.219.32.78",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.20.248",
            "10.219.5.136",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.47.66",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.26.152",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.42.72",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.18.88",
            "10.219.36.235",
            "10.219.56.91",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.147.76",
            "10.219.148.67",
            "10.219.188.151",
            "10.219.25.147",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.120.83",
            "10.219.130.19",
            "10.219.2.175",
            "10.219.114.9",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "type_m2_4xlarge": {
        "children": [],
        "hosts": [
            "54.86.112.246",
            "54.86.109.121",
            "54.86.94.44",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.185.247",
            "54.84.222.25",
            "54.84.252.121",
            "54.84.242.116",
            "54.85.157.183",
            "54.209.177.56",
            "54.85.47.190",
            "54.86.51.77",
            "54.85.175.102",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.137.179",
            "54.85.32.12",
            "54.84.189.79",
            "54.85.52.37",
            "54.84.31.76",
            "54.84.75.99",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.109.129",
            "54.84.92.185",
            "54.84.148.213",
            "54.84.125.108",
            "54.85.13.176",
            "54.85.53.103",
            "54.85.146.9",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.86.23.145",
            "54.84.156.195",
            "54.86.119.45",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.117.146",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.105.247",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.127.193",
            "10.219.90.109",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.103.178",
            "10.219.83.87",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.186.145",
            "10.219.131.134",
            "10.219.186.171",
            "10.219.156.153",
            "10.219.167.28",
            "10.219.173.21",
            "10.219.155.57",
            "10.219.141.55",
            "10.219.165.236",
            "10.219.152.142",
            "10.219.61.154",
            "10.219.6.165",
            "10.219.11.12",
            "10.219.28.78",
            "10.219.32.233",
            "10.219.1.1",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.2.93",
            "10.219.35.86",
            "10.219.51.0"
        ],
        "vars": {}
    },
    "type_t1_micro": {
        "children": [],
        "hosts": [
            "10.217.79.144"
        ],
        "vars": {}
    },
    "us-east-1": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com",
            "ec2-50-19-44-148.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.84.41.152",
            "54.84.65.195",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.28.140",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "54.84.37.150",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.189.190",
            "54.84.122.210",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.75.99",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.86.101.162",
            "54.208.124.14",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "54.208.96.71",
            "54.84.92.185",
            "54.84.42.12",
            "54.84.148.213",
            "54.84.149.25",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.86.23.145",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.217.79.144",
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.123.163",
            "10.219.92.102",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.119.218",
            "10.219.92.169",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.115.77",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.107.101",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.112.202",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.118.52",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.164.166",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.131.132",
            "10.219.160.142",
            "10.219.179.119",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.136.115",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.132.135",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.164.210",
            "10.219.161.181",
            "10.219.144.224",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.129.226",
            "10.219.142.198",
            "10.219.152.142",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.23.181",
            "10.219.14.89",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.61.154",
            "10.219.43.120",
            "10.219.26.182",
            "10.219.33.86",
            "10.219.57.225",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.50.248",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.26.121",
            "10.219.59.57",
            "10.219.41.51",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.12.148",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.25.147",
            "10.219.29.254",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.2.175",
            "10.219.111.13",
            "10.219.114.9",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "us-east-1a": {
        "children": [],
        "hosts": [
            "ec2-50-17-62-124.compute-1.amazonaws.com",
            "ec2-54-221-223-232.compute-1.amazonaws.com",
            "ec2-54-204-191-195.compute-1.amazonaws.com",
            "54.208.124.14",
            "ec2-54-197-167-3.compute-1.amazonaws.com",
            "ec2-23-22-96-198.compute-1.amazonaws.com",
            "ec2-54-204-188-107.compute-1.amazonaws.com",
            "ec2-54-205-127-141.compute-1.amazonaws.com",
            "ec2-54-198-214-42.compute-1.amazonaws.com",
            "54.208.96.71",
            "54.84.92.185",
            "54.84.42.12",
            "54.84.148.213",
            "54.84.149.25",
            "54.84.99.227",
            "54.84.125.108",
            "54.84.180.204",
            "54.84.156.145",
            "54.84.103.231",
            "54.85.13.176",
            "54.84.217.136",
            "54.84.207.241",
            "54.85.33.186",
            "54.85.53.103",
            "54.84.84.30",
            "54.85.80.174",
            "54.84.23.79",
            "54.85.10.98",
            "54.85.54.254",
            "54.85.146.9",
            "54.84.46.105",
            "54.85.90.7",
            "54.85.161.87",
            "54.208.141.20",
            "54.84.169.33",
            "54.85.200.49",
            "54.208.87.90",
            "54.85.42.61",
            "54.85.135.14",
            "54.85.84.167",
            "54.84.190.144",
            "54.209.127.172",
            "54.85.61.212",
            "54.209.74.106",
            "54.84.174.209",
            "54.209.204.12",
            "54.84.54.49",
            "54.84.163.82",
            "54.85.87.129",
            "54.85.48.128",
            "54.84.21.94",
            "54.85.80.156",
            "54.209.183.210",
            "54.209.162.114",
            "54.85.193.109",
            "54.84.18.13",
            "54.86.23.145",
            "54.85.14.238",
            "54.86.57.201",
            "54.85.53.185",
            "54.86.50.215",
            "54.84.193.141",
            "54.86.85.22",
            "54.84.156.195",
            "54.86.74.37",
            "54.86.53.153",
            "54.86.117.163",
            "54.86.117.161",
            "54.86.102.132",
            "54.86.117.236",
            "54.86.82.149",
            "54.86.71.155",
            "54.86.103.5",
            "54.86.97.73",
            "54.86.97.67",
            "54.86.90.204",
            "54.85.193.223",
            "54.85.149.164",
            "54.86.97.174",
            "54.86.96.151",
            "54.86.97.227",
            "54.86.100.62",
            "54.86.94.149",
            "54.86.98.67",
            "54.86.112.106",
            "54.86.112.96",
            "54.86.90.142",
            "54.86.90.15",
            "54.86.78.119",
            "54.86.80.163",
            "54.86.99.249",
            "54.84.167.146",
            "54.86.65.171",
            "54.86.81.225",
            "54.86.67.89",
            "54.86.87.183",
            "54.86.106.242",
            "54.86.79.232",
            "54.86.108.101",
            "54.86.98.77",
            "54.85.77.167",
            "54.86.85.33",
            "54.86.10.255",
            "54.86.80.199",
            "54.86.48.214",
            "54.84.152.213",
            "54.86.119.45",
            "54.86.107.51",
            "54.86.141.183",
            "54.85.69.157",
            "10.219.23.181",
            "10.219.14.89",
            "10.219.53.81",
            "10.219.47.252",
            "10.219.61.154",
            "10.219.43.120",
            "10.219.26.182",
            "10.219.33.86",
            "10.219.57.225",
            "10.219.43.249",
            "10.219.16.100",
            "10.219.6.165",
            "10.219.50.248",
            "10.219.4.181",
            "10.219.1.9",
            "10.219.11.12",
            "10.219.62.184",
            "10.219.52.143",
            "10.219.36.226",
            "10.219.28.78",
            "10.219.18.251",
            "10.219.31.47",
            "10.219.25.43",
            "10.219.16.141",
            "10.219.32.233",
            "10.219.49.54",
            "10.219.48.166",
            "10.219.12.85",
            "10.219.63.147",
            "10.219.47.1",
            "10.219.49.237",
            "10.219.63.105",
            "10.219.26.121",
            "10.219.59.57",
            "10.219.41.51",
            "10.219.1.1",
            "10.219.60.213",
            "10.219.12.148",
            "10.219.5.111",
            "10.219.40.115",
            "10.219.0.222",
            "10.219.17.208",
            "10.219.12.146",
            "10.219.15.194",
            "10.219.56.12",
            "10.219.3.208",
            "10.219.29.108",
            "10.219.54.28",
            "10.219.48.23",
            "10.219.63.67",
            "10.219.25.26",
            "10.219.39.144",
            "10.219.37.47",
            "10.219.47.118",
            "10.219.43.2",
            "10.219.39.139",
            "10.219.48.124",
            "10.219.2.224",
            "10.219.4.55",
            "10.219.14.143",
            "10.219.16.66",
            "10.219.5.147",
            "10.219.11.70",
            "10.219.57.108",
            "10.219.30.68",
            "10.219.56.242",
            "10.219.62.128",
            "10.219.38.61",
            "10.219.59.221",
            "10.219.8.78",
            "10.219.4.113",
            "10.219.41.127",
            "10.219.55.210",
            "10.219.2.93",
            "10.219.60.102",
            "10.219.26.28",
            "10.219.39.9",
            "10.219.11.190",
            "10.219.36.102",
            "10.219.49.11",
            "10.219.51.115",
            "10.219.17.109",
            "10.219.9.213",
            "10.219.35.86",
            "10.219.41.230",
            "10.219.41.191",
            "10.219.60.118",
            "10.219.45.70",
            "10.219.36.162",
            "10.219.56.83",
            "10.219.16.89",
            "10.219.9.203",
            "10.219.37.213",
            "10.219.19.226",
            "10.219.24.179",
            "10.219.59.159",
            "10.219.18.12",
            "10.219.36.26",
            "10.219.63.214",
            "10.219.32.78",
            "10.219.2.72",
            "10.219.27.75",
            "10.219.10.200",
            "10.219.27.228",
            "10.219.20.248",
            "10.219.53.235",
            "10.219.25.150",
            "10.219.5.136",
            "10.219.11.33",
            "10.219.40.153",
            "10.219.53.83",
            "10.219.20.163",
            "10.219.52.205",
            "10.219.47.66",
            "10.219.13.250",
            "10.219.36.177",
            "10.219.32.235",
            "10.219.5.238",
            "10.219.18.78",
            "10.219.41.67",
            "10.219.62.192",
            "10.219.63.95",
            "10.219.6.136",
            "10.219.26.152",
            "10.219.28.211",
            "10.219.22.111",
            "10.219.10.83",
            "10.219.9.24",
            "10.219.49.157",
            "10.219.42.72",
            "10.219.18.43",
            "10.219.12.138",
            "10.219.3.22",
            "10.219.32.15",
            "10.219.24.227",
            "10.219.30.9",
            "10.219.41.239",
            "10.219.61.3",
            "10.219.31.244",
            "10.219.9.54",
            "10.219.62.182",
            "10.219.18.88",
            "10.219.50.231",
            "10.219.39.194",
            "10.219.36.235",
            "10.219.56.44",
            "10.219.56.91",
            "10.219.4.79",
            "10.219.51.0",
            "10.219.49.160",
            "10.219.1.219",
            "10.219.43.48",
            "10.219.43.57",
            "10.219.16.214",
            "10.219.25.147",
            "10.219.29.254",
            "10.219.10.116",
            "10.219.45.160",
            "10.219.62.215",
            "10.219.4.252",
            "10.219.2.175",
            "10.219.58.233"
        ],
        "vars": {}
    },
    "us-east-1b": {
        "children": [],
        "hosts": [
            "ec2-54-205-251-95.compute-1.amazonaws.com",
            "54.86.112.246",
            "54.86.109.121",
            "54.86.128.114",
            "54.86.94.44",
            "54.86.103.185",
            "54.86.141.187",
            "54.84.41.152",
            "54.84.65.195",
            "54.84.87.73",
            "54.208.10.193",
            "54.84.15.178",
            "54.84.142.102",
            "54.84.185.247",
            "54.84.206.192",
            "54.84.189.117",
            "54.84.80.225",
            "54.84.222.25",
            "54.84.252.121",
            "54.85.28.140",
            "54.84.191.190",
            "54.85.42.39",
            "54.85.21.183",
            "54.85.71.54",
            "54.84.166.253",
            "54.84.170.133",
            "54.84.74.125",
            "54.85.65.51",
            "54.84.242.116",
            "54.85.68.39",
            "54.84.228.141",
            "54.85.148.101",
            "54.85.157.183",
            "54.85.199.140",
            "54.209.108.61",
            "54.84.245.20",
            "54.84.192.78",
            "54.84.240.188",
            "54.85.119.67",
            "54.209.139.239",
            "54.209.76.22",
            "54.84.103.10",
            "54.209.108.176",
            "54.208.187.98",
            "54.85.173.90",
            "54.85.160.181",
            "54.208.89.118",
            "54.209.203.222",
            "54.209.14.115",
            "54.85.249.26",
            "54.84.251.0",
            "54.85.27.197",
            "54.209.177.56",
            "54.85.47.190",
            "54.84.0.249",
            "54.86.51.77",
            "54.86.40.17",
            "54.86.76.41",
            "54.85.148.231",
            "54.86.14.157",
            "54.86.75.79",
            "54.85.175.102",
            "54.86.52.195",
            "54.86.110.115",
            "54.86.111.80",
            "54.86.89.186",
            "54.86.94.75",
            "54.86.104.18",
            "54.86.116.199",
            "54.86.87.25",
            "54.86.91.120",
            "54.86.92.153",
            "54.86.60.192",
            "54.86.8.229",
            "54.86.76.239",
            "54.86.97.144",
            "54.86.93.172",
            "54.86.97.181",
            "54.86.97.99",
            "54.86.99.25",
            "54.86.112.135",
            "54.86.111.203",
            "54.86.90.177",
            "54.86.80.208",
            "54.86.94.238",
            "54.86.64.168",
            "54.86.81.213",
            "54.86.61.31",
            "54.86.84.127",
            "54.86.53.77",
            "54.86.106.243",
            "54.86.106.244",
            "54.86.80.182",
            "54.86.108.117",
            "54.86.108.119",
            "54.85.98.144",
            "54.86.88.208",
            "54.86.81.117",
            "10.219.68.240",
            "10.219.101.208",
            "10.219.69.7",
            "10.219.72.12",
            "10.219.70.210",
            "10.219.117.146",
            "10.219.92.107",
            "10.219.85.120",
            "10.219.64.89",
            "10.219.95.221",
            "10.217.79.144",
            "10.219.100.237",
            "10.219.64.217",
            "10.219.115.245",
            "10.219.78.69",
            "10.219.123.163",
            "10.219.92.102",
            "10.219.86.78",
            "10.219.90.31",
            "10.219.127.168",
            "10.219.68.99",
            "10.219.105.247",
            "10.219.98.192",
            "10.219.127.143",
            "10.219.98.174",
            "10.219.113.16",
            "10.219.100.34",
            "10.219.85.37",
            "10.219.65.35",
            "10.219.107.166",
            "10.219.91.14",
            "10.219.84.105",
            "10.219.81.15",
            "10.219.118.63",
            "10.219.126.78",
            "10.219.107.232",
            "10.219.85.245",
            "10.219.72.93",
            "10.219.125.232",
            "10.219.81.130",
            "10.219.127.193",
            "10.219.91.234",
            "10.219.103.26",
            "10.219.119.218",
            "10.219.92.169",
            "10.219.94.77",
            "10.219.72.134",
            "10.219.90.109",
            "10.219.115.77",
            "10.219.67.120",
            "10.219.103.150",
            "10.219.107.101",
            "10.219.86.47",
            "10.219.103.216",
            "10.219.93.172",
            "10.219.109.28",
            "10.219.121.80",
            "10.219.109.92",
            "10.219.68.47",
            "10.219.97.207",
            "10.219.88.75",
            "10.219.78.42",
            "10.219.89.30",
            "10.219.85.31",
            "10.219.92.64",
            "10.219.122.228",
            "10.219.100.175",
            "10.219.111.113",
            "10.219.89.90",
            "10.219.82.113",
            "10.219.67.44",
            "10.219.112.202",
            "10.219.118.126",
            "10.219.97.164",
            "10.219.103.178",
            "10.219.81.29",
            "10.219.108.141",
            "10.219.120.23",
            "10.219.90.205",
            "10.219.118.52",
            "10.219.121.158",
            "10.219.79.157",
            "10.219.64.207",
            "10.219.112.253",
            "10.219.83.87",
            "10.219.85.43",
            "10.219.79.196",
            "10.219.114.207",
            "10.219.96.145",
            "10.219.64.87",
            "10.219.66.9",
            "10.219.117.252",
            "10.219.94.27",
            "10.219.111.126",
            "10.219.81.201",
            "10.219.77.13",
            "10.219.114.130",
            "10.219.73.211",
            "10.219.123.229",
            "10.219.75.209",
            "10.219.75.150",
            "10.219.78.250",
            "10.219.68.180",
            "10.219.114.210",
            "10.219.109.144",
            "10.219.110.47",
            "10.219.118.148",
            "10.219.119.127",
            "10.219.68.40",
            "10.219.119.27",
            "10.219.97.127",
            "10.219.115.61",
            "10.219.91.109",
            "10.219.127.169",
            "10.219.98.173",
            "10.219.68.254",
            "10.219.92.4",
            "10.219.78.180",
            "10.219.77.162",
            "10.219.66.5",
            "10.219.75.107",
            "10.219.71.164",
            "10.219.74.178",
            "10.219.119.78",
            "10.219.97.123",
            "10.219.125.7",
            "10.219.124.145",
            "10.219.64.58",
            "10.219.89.22",
            "10.219.67.205",
            "10.219.87.56",
            "10.219.102.143",
            "10.219.101.155",
            "10.219.93.219",
            "10.219.71.223",
            "10.219.84.189",
            "10.219.114.174",
            "10.219.87.108",
            "10.219.80.212",
            "10.219.91.91",
            "10.219.111.100",
            "10.219.120.83",
            "10.219.111.13",
            "10.219.114.9"
        ],
        "vars": {}
    },
    "us-east-1c": {
        "children": [],
        "hosts": [
            "ec2-54-242-229-223.compute-1.amazonaws.com",
            "ec2-50-19-44-148.compute-1.amazonaws.com",
            "ec2-54-80-236-42.compute-1.amazonaws.com",
            "ec2-174-129-105-52.compute-1.amazonaws.com",
            "ec2-23-20-41-80.compute-1.amazonaws.com",
            "ec2-54-237-120-196.compute-1.amazonaws.com",
            "ec2-50-16-237-144.compute-1.amazonaws.com",
            "54.84.37.150",
            "54.84.84.233",
            "54.84.149.162",
            "54.84.155.209",
            "54.84.164.51",
            "54.84.222.7",
            "54.84.164.99",
            "54.84.199.223",
            "54.84.189.190",
            "54.84.122.210",
            "54.84.137.179",
            "54.85.34.98",
            "54.84.97.29",
            "54.84.116.38",
            "54.85.52.64",
            "54.85.66.59",
            "54.85.32.12",
            "54.85.71.17",
            "54.85.45.216",
            "54.85.69.123",
            "54.84.47.238",
            "54.85.72.146",
            "54.86.39.175",
            "54.85.76.42",
            "54.84.190.109",
            "54.85.91.87",
            "54.85.181.37",
            "54.85.16.252",
            "54.84.189.79",
            "54.208.59.237",
            "54.208.210.176",
            "54.209.120.55",
            "54.209.106.125",
            "54.85.95.0",
            "54.208.45.55",
            "54.85.102.208",
            "54.208.12.112",
            "54.85.48.70",
            "54.85.85.59",
            "54.85.255.219",
            "54.85.47.154",
            "54.85.44.185",
            "54.85.223.164",
            "54.84.245.162",
            "54.85.166.231",
            "54.208.228.127",
            "54.85.208.32",
            "54.85.52.37",
            "54.84.31.76",
            "54.85.126.177",
            "54.84.75.99",
            "54.85.75.200",
            "54.84.114.2",
            "54.86.75.36",
            "54.85.170.154",
            "54.85.248.82",
            "54.85.167.62",
            "54.86.84.64",
            "54.86.77.91",
            "54.86.99.19",
            "54.85.37.235",
            "54.86.54.174",
            "54.86.81.21",
            "54.86.110.180",
            "54.86.117.162",
            "54.86.116.105",
            "54.86.117.237",
            "54.86.105.40",
            "54.86.78.51",
            "54.85.196.193",
            "54.86.55.72",
            "54.85.207.233",
            "54.84.199.152",
            "54.84.81.3",
            "54.86.88.52",
            "54.86.98.158",
            "54.85.75.4",
            "54.85.11.117",
            "54.86.3.216",
            "54.86.111.175",
            "54.86.90.152",
            "54.86.111.172",
            "54.86.112.102",
            "54.86.60.175",
            "54.86.80.36",
            "54.86.101.141",
            "54.86.90.71",
            "54.84.241.208",
            "54.86.104.169",
            "54.86.45.250",
            "54.85.127.222",
            "54.86.106.241",
            "54.85.251.175",
            "54.86.38.49",
            "54.86.108.102",
            "54.86.98.21",
            "54.86.89.139",
            "54.86.56.174",
            "54.86.109.129",
            "54.86.125.136",
            "54.86.141.184",
            "54.86.101.162",
            "10.219.164.166",
            "10.219.134.206",
            "10.219.157.181",
            "10.219.171.92",
            "10.219.132.7",
            "10.219.147.195",
            "10.219.179.164",
            "10.219.136.17",
            "10.219.136.66",
            "10.219.145.78",
            "10.219.173.93",
            "10.219.168.89",
            "10.219.186.145",
            "10.219.190.234",
            "10.219.173.45",
            "10.219.128.227",
            "10.219.154.184",
            "10.219.174.165",
            "10.219.183.156",
            "10.219.181.82",
            "10.219.182.240",
            "10.219.189.153",
            "10.219.146.30",
            "10.219.131.134",
            "10.219.166.184",
            "10.219.177.243",
            "10.219.150.111",
            "10.219.137.198",
            "10.219.130.190",
            "10.219.169.253",
            "10.219.130.240",
            "10.219.131.132",
            "10.219.160.142",
            "10.219.179.119",
            "10.219.130.229",
            "10.219.154.94",
            "10.219.153.220",
            "10.219.168.41",
            "10.219.137.105",
            "10.219.188.5",
            "10.219.186.171",
            "10.219.136.115",
            "10.219.155.180",
            "10.219.154.115",
            "10.219.185.186",
            "10.219.137.205",
            "10.219.145.106",
            "10.219.138.98",
            "10.219.184.152",
            "10.219.143.130",
            "10.219.154.203",
            "10.219.187.178",
            "10.219.146.42",
            "10.219.143.228",
            "10.219.163.166",
            "10.219.136.13",
            "10.219.184.234",
            "10.219.154.12",
            "10.219.180.244",
            "10.219.169.68",
            "10.219.130.1",
            "10.219.142.79",
            "10.219.158.176",
            "10.219.133.48",
            "10.219.132.135",
            "10.219.156.153",
            "10.219.165.216",
            "10.219.167.28",
            "10.219.169.240",
            "10.219.177.150",
            "10.219.173.21",
            "10.219.178.85",
            "10.219.155.123",
            "10.219.178.84",
            "10.219.140.138",
            "10.219.165.155",
            "10.219.153.9",
            "10.219.138.5",
            "10.219.152.17",
            "10.219.189.219",
            "10.219.173.38",
            "10.219.191.53",
            "10.219.155.57",
            "10.219.134.179",
            "10.219.141.55",
            "10.219.173.37",
            "10.219.147.63",
            "10.219.142.242",
            "10.219.149.40",
            "10.219.154.211",
            "10.219.177.41",
            "10.219.138.185",
            "10.219.169.135",
            "10.219.142.152",
            "10.219.180.178",
            "10.219.155.112",
            "10.219.152.253",
            "10.219.161.92",
            "10.219.129.154",
            "10.219.150.33",
            "10.219.163.151",
            "10.219.142.223",
            "10.219.185.101",
            "10.219.187.219",
            "10.219.137.49",
            "10.219.185.140",
            "10.219.183.41",
            "10.219.128.18",
            "10.219.137.67",
            "10.219.136.200",
            "10.219.167.0",
            "10.219.166.38",
            "10.219.147.74",
            "10.219.134.176",
            "10.219.185.71",
            "10.219.162.164",
            "10.219.159.21",
            "10.219.183.205",
            "10.219.131.26",
            "10.219.130.129",
            "10.219.177.177",
            "10.219.165.247",
            "10.219.142.23",
            "10.219.158.35",
            "10.219.128.183",
            "10.219.179.156",
            "10.219.132.1",
            "10.219.151.162",
            "10.219.175.97",
            "10.219.133.98",
            "10.219.175.162",
            "10.219.168.254",
            "10.219.135.107",
            "10.219.147.25",
            "10.219.140.250",
            "10.219.156.2",
            "10.219.143.239",
            "10.219.150.186",
            "10.219.175.103",
            "10.219.154.60",
            "10.219.164.210",
            "10.219.161.181",
            "10.219.144.224",
            "10.219.165.236",
            "10.219.184.95",
            "10.219.147.27",
            "10.219.132.76",
            "10.219.129.226",
            "10.219.142.198",
            "10.219.152.142",
            "10.219.182.219",
            "10.219.154.235",
            "10.219.177.248",
            "10.219.147.76",
            "10.219.164.5",
            "10.219.134.89",
            "10.219.148.67",
            "10.219.161.188",
            "10.219.188.151",
            "10.219.152.52",
            "10.219.161.118",
            "10.219.132.127",
            "10.219.130.19",
            "10.219.152.208",
            "10.219.167.181",
            "10.219.166.102",
            "10.219.174.231"
        ],
        "vars": {}
    }
}

host_vars = {}

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--list', action='store_true', dest='list')
    parser.add_option('--host', dest='hostname', default='')
    options, args = parser.parse_args()
    if options.list:
        json.dump(inventory_dict, sys.stdout, indent=4)
    elif options.hostname:
        json.dump(host_vars, sys.stdout, indent=4)
    else:
        json.dump({}, sys.stdout, indent=4)

#!/usr/bin/env python

# Python
import json
import optparse

inv_list = {
  "ansible1.axialmarket.com": [
    "ec2-54-226-227-106.compute-1.amazonaws.com"
  ], 
  "ansible2.axialmarket.com": [
    "ec2-54-227-113-75.compute-1.amazonaws.com"
  ], 
  "app1new.axialmarket.com": [
    "ec2-54-235-143-131.compute-1.amazonaws.com"
  ], 
  "app2new.axialmarket.com": [
    "ec2-54-235-143-132.compute-1.amazonaws.com"
  ], 
  "app2t.axialmarket.com": [
    "ec2-23-23-168-208.compute-1.amazonaws.com"
  ], 
  "app2t.dev.axialmarket.com": [
    "ec2-23-23-168-208.compute-1.amazonaws.com"
  ], 
  "awx.axialmarket.com": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "axtdev2.axialmarket.com": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "backup1.axialmarket.com": [
    "ec2-23-23-170-30.compute-1.amazonaws.com"
  ], 
  "bah.axialmarket.com": [
    "ec2-107-20-176-139.compute-1.amazonaws.com"
  ], 
  "bennew.axialmarket.com": [
    "ec2-54-243-146-75.compute-1.amazonaws.com"
  ], 
  "build0.axialmarket.com": [
    "ec2-54-226-244-191.compute-1.amazonaws.com"
  ], 
  "cburke0.axialmarket.com": [
    "ec2-54-226-100-117.compute-1.amazonaws.com"
  ], 
  "dabnew.axialmarket.com": [
    "ec2-107-22-248-113.compute-1.amazonaws.com"
  ], 
  "dannew.axialmarket.com": [
    "ec2-107-22-247-88.compute-1.amazonaws.com"
  ], 
  "de1-intenv.axialmarket.com": [
    "ec2-54-224-92-80.compute-1.amazonaws.com"
  ], 
  "dev11-20120311": [
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "dev11-20130828": [
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "dev11-20130903-dab": [
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "firecrow.axialmarket.com": [
    "ec2-54-227-30-105.compute-1.amazonaws.com"
  ], 
  "herby0.axialmarket.com": [
    "ec2-174-129-140-30.compute-1.amazonaws.com"
  ], 
  "i-02966c7a": [
    "ec2-23-21-57-109.compute-1.amazonaws.com"
  ], 
  "i-0485b47c": [
    "ec2-23-23-168-208.compute-1.amazonaws.com"
  ], 
  "i-0805a578": [
    "ec2-107-22-234-22.compute-1.amazonaws.com"
  ], 
  "i-0a1e4777": [
    "ec2-75-101-129-169.compute-1.amazonaws.com"
  ], 
  "i-0e05a57e": [
    "ec2-107-22-234-180.compute-1.amazonaws.com"
  ], 
  "i-116f5861": [
    "ec2-54-235-143-162.compute-1.amazonaws.com"
  ], 
  "i-197edf79": [
    "ec2-54-226-244-191.compute-1.amazonaws.com"
  ], 
  "i-26008355": [
    "ec2-75-101-157-248.compute-1.amazonaws.com"
  ], 
  "i-2ff6135e": [
    "ec2-54-242-36-133.compute-1.amazonaws.com"
  ], 
  "i-3cbc6d50": [
    "ec2-54-234-233-19.compute-1.amazonaws.com"
  ], 
  "i-3e9a7f5b": [
    "ec2-54-224-92-80.compute-1.amazonaws.com"
  ], 
  "i-43f6a533": [
    "ec2-54-235-143-131.compute-1.amazonaws.com"
  ], 
  "i-45906822": [
    "ec2-23-21-100-222.compute-1.amazonaws.com"
  ], 
  "i-508c1923": [
    "ec2-23-23-130-201.compute-1.amazonaws.com"
  ], 
  "i-52970021": [
    "ec2-23-23-169-133.compute-1.amazonaws.com"
  ], 
  "i-57cc2c25": [
    "ec2-54-225-229-159.compute-1.amazonaws.com"
  ], 
  "i-59f23536": [
    "ec2-75-101-128-47.compute-1.amazonaws.com"
  ], 
  "i-7012b200": [
    "ec2-107-22-249-212.compute-1.amazonaws.com"
  ], 
  "i-73fead03": [
    "ec2-54-235-143-132.compute-1.amazonaws.com"
  ], 
  "i-75faa905": [
    "ec2-54-235-143-133.compute-1.amazonaws.com"
  ], 
  "i-76e49b0e": [
    "ec2-75-101-128-224.compute-1.amazonaws.com"
  ], 
  "i-78c9450b": [
    "ec2-54-225-88-116.compute-1.amazonaws.com"
  ], 
  "i-7aa18911": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "i-7dfdae0d": [
    "ec2-54-235-143-134.compute-1.amazonaws.com"
  ], 
  "i-8559d6fa": [
    "ec2-23-21-224-105.compute-1.amazonaws.com"
  ], 
  "i-899768e4": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "i-918130fb": [
    "ec2-174-129-171-101.compute-1.amazonaws.com"
  ], 
  "i-99ce0ceb": [
    "ec2-107-22-234-92.compute-1.amazonaws.com"
  ], 
  "i-9a450df8": [
    "ec2-50-19-184-148.compute-1.amazonaws.com"
  ], 
  "i-9fce0ced": [
    "ec2-107-20-176-139.compute-1.amazonaws.com"
  ], 
  "i-a80682c4": [
    "ec2-54-235-65-26.compute-1.amazonaws.com"
  ], 
  "i-b43ab5df": [
    "ec2-174-129-140-30.compute-1.amazonaws.com"
  ], 
  "i-baa893c2": [
    "ec2-23-23-170-30.compute-1.amazonaws.com"
  ], 
  "i-bc23a0cf": [
    "ec2-75-101-159-82.compute-1.amazonaws.com"
  ], 
  "i-bed948cd": [
    "ec2-54-235-112-3.compute-1.amazonaws.com"
  ], 
  "i-c200c4a8": [
    "ec2-54-227-30-105.compute-1.amazonaws.com"
  ], 
  "i-c69ae2be": [
    "ec2-23-21-133-17.compute-1.amazonaws.com"
  ], 
  "i-c6d33fa3": [
    "ec2-54-226-100-117.compute-1.amazonaws.com"
  ], 
  "i-cc4d2abf": [
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "i-cc9c3fbc": [
    "ec2-54-243-146-75.compute-1.amazonaws.com"
  ], 
  "i-d01dacb3": [
    "ec2-54-234-218-33.compute-1.amazonaws.com"
  ], 
  "i-da6631b3": [
    "ec2-54-226-227-106.compute-1.amazonaws.com"
  ], 
  "i-dc6631b5": [
    "ec2-54-227-113-75.compute-1.amazonaws.com"
  ], 
  "i-f005a580": [
    "ec2-107-22-241-13.compute-1.amazonaws.com"
  ], 
  "i-f605a586": [
    "ec2-107-22-247-88.compute-1.amazonaws.com"
  ], 
  "i-f805a588": [
    "ec2-107-22-248-113.compute-1.amazonaws.com"
  ], 
  "i-f9829894": [
    "ec2-54-225-172-84.compute-1.amazonaws.com"
  ], 
  "inf.axialmarket.com": [
    "ec2-54-225-229-159.compute-1.amazonaws.com"
  ], 
  "jeffnew.axialmarket.com": [
    "ec2-107-22-234-180.compute-1.amazonaws.com"
  ], 
  "jenkins.axialmarket.com": [
    "ec2-23-21-224-105.compute-1.amazonaws.com"
  ], 
  "jump.axialmarket.com": [
    "ec2-23-23-169-133.compute-1.amazonaws.com"
  ], 
  "key_Dana_Spiegel": [
    "ec2-50-19-184-148.compute-1.amazonaws.com"
  ], 
  "key_bah-20130614": [
    "ec2-54-234-218-33.compute-1.amazonaws.com", 
    "ec2-54-226-244-191.compute-1.amazonaws.com"
  ], 
  "key_herby-axial-20130903": [
    "ec2-54-224-92-80.compute-1.amazonaws.com"
  ], 
  "key_herbyg-axial-201308": [
    "ec2-54-211-252-32.compute-1.amazonaws.com", 
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "key_ike-20120322": [
    "ec2-23-21-100-222.compute-1.amazonaws.com", 
    "ec2-23-21-57-109.compute-1.amazonaws.com", 
    "ec2-75-101-128-224.compute-1.amazonaws.com", 
    "ec2-23-21-133-17.compute-1.amazonaws.com", 
    "ec2-23-23-168-208.compute-1.amazonaws.com", 
    "ec2-23-23-170-30.compute-1.amazonaws.com", 
    "ec2-75-101-129-169.compute-1.amazonaws.com", 
    "ec2-23-21-224-105.compute-1.amazonaws.com", 
    "ec2-54-242-36-133.compute-1.amazonaws.com", 
    "ec2-107-22-234-22.compute-1.amazonaws.com", 
    "ec2-107-22-234-180.compute-1.amazonaws.com", 
    "ec2-107-22-241-13.compute-1.amazonaws.com", 
    "ec2-107-22-247-88.compute-1.amazonaws.com", 
    "ec2-107-22-248-113.compute-1.amazonaws.com", 
    "ec2-107-22-249-212.compute-1.amazonaws.com", 
    "ec2-54-243-146-75.compute-1.amazonaws.com", 
    "ec2-54-235-143-131.compute-1.amazonaws.com", 
    "ec2-54-235-143-133.compute-1.amazonaws.com", 
    "ec2-54-235-143-132.compute-1.amazonaws.com", 
    "ec2-54-235-143-134.compute-1.amazonaws.com", 
    "ec2-54-235-143-162.compute-1.amazonaws.com", 
    "ec2-75-101-157-248.compute-1.amazonaws.com", 
    "ec2-75-101-159-82.compute-1.amazonaws.com", 
    "ec2-54-225-88-116.compute-1.amazonaws.com", 
    "ec2-23-23-169-133.compute-1.amazonaws.com", 
    "ec2-54-235-112-3.compute-1.amazonaws.com", 
    "ec2-54-225-229-159.compute-1.amazonaws.com", 
    "ec2-107-22-234-92.compute-1.amazonaws.com", 
    "ec2-107-20-176-139.compute-1.amazonaws.com", 
    "ec2-54-225-172-84.compute-1.amazonaws.com"
  ], 
  "key_matt-20120423": [
    "ec2-54-226-227-106.compute-1.amazonaws.com", 
    "ec2-54-227-113-75.compute-1.amazonaws.com", 
    "ec2-54-235-65-26.compute-1.amazonaws.com", 
    "ec2-174-129-171-101.compute-1.amazonaws.com", 
    "ec2-54-234-233-19.compute-1.amazonaws.com", 
    "ec2-174-129-140-30.compute-1.amazonaws.com", 
    "ec2-54-227-30-105.compute-1.amazonaws.com", 
    "ec2-54-226-100-117.compute-1.amazonaws.com"
  ], 
  "key_mike-20121126": [
    "ec2-75-101-128-47.compute-1.amazonaws.com", 
    "ec2-23-23-130-201.compute-1.amazonaws.com", 
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "logstore1.axialmarket.com": [
    "ec2-75-101-129-169.compute-1.amazonaws.com"
  ], 
  "logstore2.axialmarket.com": [
    "ec2-54-235-112-3.compute-1.amazonaws.com"
  ], 
  "mattnew.axialmarket.com": [
    "ec2-107-22-241-13.compute-1.amazonaws.com"
  ], 
  "monitor0.axialmarket.com": [
    "ec2-54-235-65-26.compute-1.amazonaws.com"
  ], 
  "mx0.axialmarket.com": [
    "ec2-23-21-57-109.compute-1.amazonaws.com"
  ], 
  "mx0a.axialmarket.com": [
    "ec2-23-21-224-105.compute-1.amazonaws.com"
  ], 
  "mx1.axialmarket.com": [
    "ec2-75-101-128-47.compute-1.amazonaws.com"
  ], 
  "mx2.axialmarket.com": [
    "ec2-75-101-128-224.compute-1.amazonaws.com"
  ], 
  "mx5.axialmarket.com": [
    "ec2-75-101-129-169.compute-1.amazonaws.com"
  ], 
  "pak.axialmarket.com": [
    "ec2-54-242-36-133.compute-1.amazonaws.com"
  ], 
  "pak0.axialmarket.com": [
    "ec2-54-242-36-133.compute-1.amazonaws.com"
  ], 
  "poundtest1.axialmarket.com": [
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "production-db7": [
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "production-db7-rdssnap-p4hsx77hy8l5zqj": [
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "production-readonly-db7": [
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "rabbit.axialmarket.com": [
    "ec2-50-19-184-148.compute-1.amazonaws.com"
  ], 
  "rds_mysql": [
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "rds_parameter_group_axialmarket-5-5": [
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "rds_parameter_group_default_mysql5_1": [
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "rds_parameter_group_default_mysql5_5": [
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "rds_parameter_group_mysqldump": [
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "releng0.axialmarket.com": [
    "ec2-23-21-100-222.compute-1.amazonaws.com"
  ], 
  "releng1.axialmarket.com": [
    "ec2-23-21-133-17.compute-1.amazonaws.com"
  ], 
  "rexnew.axialmarket.com": [
    "ec2-54-235-143-162.compute-1.amazonaws.com"
  ], 
  "rollupy0.axialmarket.com": [
    "ec2-54-225-172-84.compute-1.amazonaws.com"
  ], 
  "security_group_MTA": [
    "ec2-75-101-128-47.compute-1.amazonaws.com", 
    "ec2-23-21-57-109.compute-1.amazonaws.com", 
    "ec2-75-101-128-224.compute-1.amazonaws.com", 
    "ec2-23-21-224-105.compute-1.amazonaws.com"
  ], 
  "security_group_WWW-PROD-2013": [
    "ec2-75-101-157-248.compute-1.amazonaws.com", 
    "ec2-75-101-159-82.compute-1.amazonaws.com"
  ], 
  "security_group_backup2012": [
    "ec2-23-23-170-30.compute-1.amazonaws.com"
  ], 
  "security_group_dataeng-test": [
    "ec2-54-224-92-80.compute-1.amazonaws.com"
  ], 
  "security_group_development-2013-Jan": [
    "ec2-54-226-227-106.compute-1.amazonaws.com", 
    "ec2-54-227-113-75.compute-1.amazonaws.com", 
    "ec2-174-129-171-101.compute-1.amazonaws.com", 
    "ec2-54-234-233-19.compute-1.amazonaws.com", 
    "ec2-54-234-218-33.compute-1.amazonaws.com", 
    "ec2-54-226-244-191.compute-1.amazonaws.com", 
    "ec2-174-129-140-30.compute-1.amazonaws.com", 
    "ec2-54-227-30-105.compute-1.amazonaws.com", 
    "ec2-54-226-100-117.compute-1.amazonaws.com", 
    "ec2-54-234-3-7.compute-1.amazonaws.com", 
    "ec2-107-22-234-22.compute-1.amazonaws.com", 
    "ec2-107-22-234-180.compute-1.amazonaws.com", 
    "ec2-107-22-241-13.compute-1.amazonaws.com", 
    "ec2-107-22-247-88.compute-1.amazonaws.com", 
    "ec2-107-22-248-113.compute-1.amazonaws.com", 
    "ec2-107-22-249-212.compute-1.amazonaws.com", 
    "ec2-54-243-146-75.compute-1.amazonaws.com", 
    "ec2-54-235-143-162.compute-1.amazonaws.com", 
    "ec2-54-225-88-116.compute-1.amazonaws.com", 
    "ec2-23-23-130-201.compute-1.amazonaws.com", 
    "ec2-107-20-160-49.compute-1.amazonaws.com", 
    "ec2-107-22-234-92.compute-1.amazonaws.com", 
    "ec2-107-20-176-139.compute-1.amazonaws.com"
  ], 
  "security_group_development-summer2012": [
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "security_group_development2012July": [
    "ec2-23-23-168-208.compute-1.amazonaws.com"
  ], 
  "security_group_inf-mgmt-2013": [
    "ec2-54-225-229-159.compute-1.amazonaws.com"
  ], 
  "security_group_jump": [
    "ec2-23-23-169-133.compute-1.amazonaws.com"
  ], 
  "security_group_monitor-GOD-2013": [
    "ec2-54-235-65-26.compute-1.amazonaws.com"
  ], 
  "security_group_pak-internal": [
    "ec2-54-242-36-133.compute-1.amazonaws.com"
  ], 
  "security_group_production": [
    "ec2-50-19-184-148.compute-1.amazonaws.com", 
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "security_group_production-NEWWORLD-201202": [
    "ec2-54-235-143-131.compute-1.amazonaws.com", 
    "ec2-54-235-143-133.compute-1.amazonaws.com", 
    "ec2-54-235-143-132.compute-1.amazonaws.com", 
    "ec2-54-235-143-134.compute-1.amazonaws.com", 
    "ec2-54-225-172-84.compute-1.amazonaws.com"
  ], 
  "security_group_production-awx": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "security_group_releng20120404": [
    "ec2-23-21-100-222.compute-1.amazonaws.com", 
    "ec2-23-21-133-17.compute-1.amazonaws.com"
  ], 
  "security_group_util-20121011": [
    "ec2-75-101-129-169.compute-1.amazonaws.com", 
    "ec2-54-235-112-3.compute-1.amazonaws.com"
  ], 
  "security_group_www-mktg": [
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "stevenew.axialmarket.com": [
    "ec2-107-22-234-92.compute-1.amazonaws.com"
  ], 
  "tag_Environment_Production": [
    "ec2-50-19-184-148.compute-1.amazonaws.com"
  ], 
  "tag_Name_INF-umgmt1": [
    "ec2-54-225-229-159.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-PROD-app1": [
    "ec2-54-235-143-131.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-PROD-app2": [
    "ec2-54-235-143-132.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-PROD-worker1": [
    "ec2-54-235-143-133.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-PROD-worker2": [
    "ec2-54-235-143-134.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-bah": [
    "ec2-107-20-176-139.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-bennew": [
    "ec2-54-243-146-75.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-dabnew": [
    "ec2-107-22-248-113.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-dannew": [
    "ec2-107-22-247-88.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-jeffnew": [
    "ec2-107-22-234-180.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-jumphost-2": [
    "ec2-23-23-169-133.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-mattnew": [
    "ec2-107-22-241-13.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-poundtest1": [
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-poundtest1_": [
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-rexnew": [
    "ec2-54-235-143-162.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-stevenew-replace": [
    "ec2-107-22-234-92.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-tannernew": [
    "ec2-23-23-130-201.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-thomasnew-2": [
    "ec2-54-225-88-116.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-willnew": [
    "ec2-107-22-234-22.compute-1.amazonaws.com"
  ], 
  "tag_Name_NEWWORLD-worker1devnew": [
    "ec2-107-22-249-212.compute-1.amazonaws.com"
  ], 
  "tag_Name_WWW-TEST": [
    "ec2-54-234-233-19.compute-1.amazonaws.com"
  ], 
  "tag_Name_WWW1-MKTG": [
    "ec2-75-101-157-248.compute-1.amazonaws.com"
  ], 
  "tag_Name_WWW2-MKTG": [
    "ec2-75-101-159-82.compute-1.amazonaws.com"
  ], 
  "tag_Name_ansible": [
    "ec2-54-226-227-106.compute-1.amazonaws.com", 
    "ec2-54-227-113-75.compute-1.amazonaws.com"
  ], 
  "tag_Name_app2t_development_axialmarket_com": [
    "ec2-23-23-168-208.compute-1.amazonaws.com"
  ], 
  "tag_Name_awx": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "tag_Name_axtdev2": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "tag_Name_backup1": [
    "ec2-23-23-170-30.compute-1.amazonaws.com"
  ], 
  "tag_Name_build_server": [
    "ec2-54-226-244-191.compute-1.amazonaws.com"
  ], 
  "tag_Name_cburke0": [
    "ec2-54-226-100-117.compute-1.amazonaws.com"
  ], 
  "tag_Name_dataeng_test1": [
    "ec2-54-224-92-80.compute-1.amazonaws.com"
  ], 
  "tag_Name_firecrow-dev": [
    "ec2-54-227-30-105.compute-1.amazonaws.com"
  ], 
  "tag_Name_herby0": [
    "ec2-174-129-140-30.compute-1.amazonaws.com"
  ], 
  "tag_Name_logstore1": [
    "ec2-75-101-129-169.compute-1.amazonaws.com"
  ], 
  "tag_Name_logstore2": [
    "ec2-54-235-112-3.compute-1.amazonaws.com"
  ], 
  "tag_Name_mx0": [
    "ec2-23-21-57-109.compute-1.amazonaws.com"
  ], 
  "tag_Name_mx0a": [
    "ec2-23-21-224-105.compute-1.amazonaws.com"
  ], 
  "tag_Name_mx1_new": [
    "ec2-75-101-128-47.compute-1.amazonaws.com"
  ], 
  "tag_Name_mx2": [
    "ec2-75-101-128-224.compute-1.amazonaws.com"
  ], 
  "tag_Name_new-testapp1": [
    "ec2-174-129-171-101.compute-1.amazonaws.com"
  ], 
  "tag_Name_pak0_axialmarket_com": [
    "ec2-54-242-36-133.compute-1.amazonaws.com"
  ], 
  "tag_Name_rabbit_axialmarket_com": [
    "ec2-50-19-184-148.compute-1.amazonaws.com"
  ], 
  "tag_Name_releng0": [
    "ec2-23-21-100-222.compute-1.amazonaws.com"
  ], 
  "tag_Name_releng1": [
    "ec2-23-21-133-17.compute-1.amazonaws.com"
  ], 
  "tag_Name_rollupy0-PROD": [
    "ec2-54-225-172-84.compute-1.amazonaws.com"
  ], 
  "tag_Name_tannernew_": [
    "ec2-23-23-130-201.compute-1.amazonaws.com"
  ], 
  "tag_Name_testapp1": [
    "ec2-54-234-218-33.compute-1.amazonaws.com"
  ], 
  "tag_Name_zabbix-upgrade": [
    "ec2-54-235-65-26.compute-1.amazonaws.com"
  ], 
  "tag_Use_RabbitMQ__celerycam__celerybeat__celeryd__postfix": [
    "ec2-50-19-184-148.compute-1.amazonaws.com"
  ], 
  "tag_environment_dev": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "tag_environment_production": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "tag_id_awx": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "tag_id_axtdev2": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "tag_os_ubuntu": [
    "ec2-54-211-252-32.compute-1.amazonaws.com", 
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "tag_primary_role_awx": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "tag_primary_role_dev": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "tag_purpose_syscleanup": [
    "ec2-23-21-100-222.compute-1.amazonaws.com"
  ], 
  "tag_role_awx_": [
    "ec2-54-211-252-32.compute-1.amazonaws.com"
  ], 
  "tag_role_dev_": [
    "ec2-54-234-3-7.compute-1.amazonaws.com"
  ], 
  "tannernew.axialmarket.com": [
    "ec2-23-23-130-201.compute-1.amazonaws.com"
  ], 
  "testapp1.axialmarket.com": [
    "ec2-174-129-171-101.compute-1.amazonaws.com"
  ], 
  "testapp2.axialmarket.com": [
    "ec2-54-234-218-33.compute-1.amazonaws.com"
  ], 
  "testnoelb.axialmarket.com": [
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "testworker1.axialmarket.com": [
    "ec2-107-22-249-212.compute-1.amazonaws.com"
  ], 
  "thomasnew.axialmarket.com": [
    "ec2-54-225-88-116.compute-1.amazonaws.com"
  ], 
  "type_db_m1_medium": [
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "type_db_m1_xlarge": [
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "type_m1_large": [
    "ec2-54-235-65-26.compute-1.amazonaws.com", 
    "ec2-174-129-171-101.compute-1.amazonaws.com", 
    "ec2-54-234-218-33.compute-1.amazonaws.com", 
    "ec2-50-19-184-148.compute-1.amazonaws.com", 
    "ec2-174-129-140-30.compute-1.amazonaws.com", 
    "ec2-54-227-30-105.compute-1.amazonaws.com", 
    "ec2-54-226-100-117.compute-1.amazonaws.com", 
    "ec2-54-224-92-80.compute-1.amazonaws.com", 
    "ec2-23-23-168-208.compute-1.amazonaws.com", 
    "ec2-54-234-3-7.compute-1.amazonaws.com", 
    "ec2-107-22-234-22.compute-1.amazonaws.com", 
    "ec2-107-22-234-180.compute-1.amazonaws.com", 
    "ec2-107-22-241-13.compute-1.amazonaws.com", 
    "ec2-107-22-247-88.compute-1.amazonaws.com", 
    "ec2-107-22-248-113.compute-1.amazonaws.com", 
    "ec2-107-22-249-212.compute-1.amazonaws.com", 
    "ec2-54-243-146-75.compute-1.amazonaws.com", 
    "ec2-54-235-143-131.compute-1.amazonaws.com", 
    "ec2-54-235-143-132.compute-1.amazonaws.com", 
    "ec2-54-235-143-162.compute-1.amazonaws.com", 
    "ec2-23-23-130-201.compute-1.amazonaws.com", 
    "ec2-107-22-234-92.compute-1.amazonaws.com", 
    "ec2-107-20-176-139.compute-1.amazonaws.com"
  ], 
  "type_m1_medium": [
    "ec2-54-226-227-106.compute-1.amazonaws.com", 
    "ec2-54-227-113-75.compute-1.amazonaws.com", 
    "ec2-54-234-233-19.compute-1.amazonaws.com", 
    "ec2-54-226-244-191.compute-1.amazonaws.com", 
    "ec2-23-21-100-222.compute-1.amazonaws.com", 
    "ec2-23-21-133-17.compute-1.amazonaws.com", 
    "ec2-54-211-252-32.compute-1.amazonaws.com", 
    "ec2-54-242-36-133.compute-1.amazonaws.com", 
    "ec2-75-101-157-248.compute-1.amazonaws.com", 
    "ec2-75-101-159-82.compute-1.amazonaws.com", 
    "ec2-54-225-88-116.compute-1.amazonaws.com", 
    "ec2-23-23-169-133.compute-1.amazonaws.com"
  ], 
  "type_m1_small": [
    "ec2-75-101-129-169.compute-1.amazonaws.com", 
    "ec2-107-20-160-49.compute-1.amazonaws.com"
  ], 
  "type_m1_xlarge": [
    "ec2-54-235-143-133.compute-1.amazonaws.com", 
    "ec2-54-235-143-134.compute-1.amazonaws.com", 
    "ec2-54-235-112-3.compute-1.amazonaws.com", 
    "ec2-54-225-172-84.compute-1.amazonaws.com"
  ], 
  "type_m2_2xlarge": [
    "ec2-23-23-170-30.compute-1.amazonaws.com"
  ], 
  "type_t1_micro": [
    "ec2-75-101-128-47.compute-1.amazonaws.com", 
    "ec2-23-21-57-109.compute-1.amazonaws.com", 
    "ec2-75-101-128-224.compute-1.amazonaws.com", 
    "ec2-23-21-224-105.compute-1.amazonaws.com", 
    "ec2-54-225-229-159.compute-1.amazonaws.com"
  ], 
  "us-east-1": [
    "ec2-54-226-227-106.compute-1.amazonaws.com", 
    "ec2-54-227-113-75.compute-1.amazonaws.com", 
    "ec2-54-235-65-26.compute-1.amazonaws.com", 
    "ec2-174-129-171-101.compute-1.amazonaws.com", 
    "ec2-54-234-233-19.compute-1.amazonaws.com", 
    "ec2-75-101-128-47.compute-1.amazonaws.com", 
    "ec2-54-234-218-33.compute-1.amazonaws.com", 
    "ec2-54-226-244-191.compute-1.amazonaws.com", 
    "ec2-50-19-184-148.compute-1.amazonaws.com", 
    "ec2-174-129-140-30.compute-1.amazonaws.com", 
    "ec2-54-227-30-105.compute-1.amazonaws.com", 
    "ec2-23-21-100-222.compute-1.amazonaws.com", 
    "ec2-54-226-100-117.compute-1.amazonaws.com", 
    "ec2-54-224-92-80.compute-1.amazonaws.com", 
    "ec2-23-21-57-109.compute-1.amazonaws.com", 
    "ec2-75-101-128-224.compute-1.amazonaws.com", 
    "ec2-23-21-133-17.compute-1.amazonaws.com", 
    "ec2-23-23-168-208.compute-1.amazonaws.com", 
    "ec2-23-23-170-30.compute-1.amazonaws.com", 
    "ec2-54-211-252-32.compute-1.amazonaws.com", 
    "ec2-54-234-3-7.compute-1.amazonaws.com", 
    "ec2-75-101-129-169.compute-1.amazonaws.com", 
    "ec2-23-21-224-105.compute-1.amazonaws.com", 
    "ec2-54-242-36-133.compute-1.amazonaws.com", 
    "ec2-107-22-234-22.compute-1.amazonaws.com", 
    "ec2-107-22-234-180.compute-1.amazonaws.com", 
    "ec2-107-22-241-13.compute-1.amazonaws.com", 
    "ec2-107-22-247-88.compute-1.amazonaws.com", 
    "ec2-107-22-248-113.compute-1.amazonaws.com", 
    "ec2-107-22-249-212.compute-1.amazonaws.com", 
    "ec2-54-243-146-75.compute-1.amazonaws.com", 
    "ec2-54-235-143-131.compute-1.amazonaws.com", 
    "ec2-54-235-143-133.compute-1.amazonaws.com", 
    "ec2-54-235-143-132.compute-1.amazonaws.com", 
    "ec2-54-235-143-134.compute-1.amazonaws.com", 
    "ec2-54-235-143-162.compute-1.amazonaws.com", 
    "ec2-75-101-157-248.compute-1.amazonaws.com", 
    "ec2-75-101-159-82.compute-1.amazonaws.com", 
    "ec2-54-225-88-116.compute-1.amazonaws.com", 
    "ec2-23-23-130-201.compute-1.amazonaws.com", 
    "ec2-23-23-169-133.compute-1.amazonaws.com", 
    "ec2-54-235-112-3.compute-1.amazonaws.com", 
    "ec2-107-20-160-49.compute-1.amazonaws.com", 
    "ec2-54-225-229-159.compute-1.amazonaws.com", 
    "ec2-107-22-234-92.compute-1.amazonaws.com", 
    "ec2-107-20-176-139.compute-1.amazonaws.com", 
    "ec2-54-225-172-84.compute-1.amazonaws.com", 
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "us-east-1c": [
    "ec2-23-21-100-222.compute-1.amazonaws.com", 
    "ec2-23-23-168-208.compute-1.amazonaws.com", 
    "ec2-75-101-129-169.compute-1.amazonaws.com", 
    "ec2-107-22-249-212.compute-1.amazonaws.com", 
    "ec2-54-235-143-132.compute-1.amazonaws.com", 
    "ec2-54-235-143-134.compute-1.amazonaws.com", 
    "ec2-75-101-157-248.compute-1.amazonaws.com", 
    "ec2-54-235-112-3.compute-1.amazonaws.com", 
    "ec2-107-20-160-49.compute-1.amazonaws.com", 
    "ec2-54-225-172-84.compute-1.amazonaws.com", 
    "dev11-20130828.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "dev11-20130903-dab.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-db7-rdssnap-p4hsx77hy8l5zqj.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "us-east-1d": [
    "ec2-54-226-227-106.compute-1.amazonaws.com", 
    "ec2-54-227-113-75.compute-1.amazonaws.com", 
    "ec2-54-235-65-26.compute-1.amazonaws.com", 
    "ec2-174-129-171-101.compute-1.amazonaws.com", 
    "ec2-54-234-233-19.compute-1.amazonaws.com", 
    "ec2-75-101-128-47.compute-1.amazonaws.com", 
    "ec2-54-234-218-33.compute-1.amazonaws.com", 
    "ec2-54-226-244-191.compute-1.amazonaws.com", 
    "ec2-50-19-184-148.compute-1.amazonaws.com", 
    "ec2-174-129-140-30.compute-1.amazonaws.com", 
    "ec2-54-227-30-105.compute-1.amazonaws.com", 
    "ec2-54-226-100-117.compute-1.amazonaws.com", 
    "ec2-54-224-92-80.compute-1.amazonaws.com", 
    "ec2-23-21-57-109.compute-1.amazonaws.com", 
    "ec2-75-101-128-224.compute-1.amazonaws.com", 
    "ec2-23-21-133-17.compute-1.amazonaws.com", 
    "ec2-54-211-252-32.compute-1.amazonaws.com", 
    "ec2-54-234-3-7.compute-1.amazonaws.com", 
    "ec2-23-21-224-105.compute-1.amazonaws.com", 
    "ec2-54-242-36-133.compute-1.amazonaws.com", 
    "ec2-107-22-234-22.compute-1.amazonaws.com", 
    "ec2-107-22-234-180.compute-1.amazonaws.com", 
    "ec2-107-22-241-13.compute-1.amazonaws.com", 
    "ec2-107-22-247-88.compute-1.amazonaws.com", 
    "ec2-107-22-248-113.compute-1.amazonaws.com", 
    "ec2-54-243-146-75.compute-1.amazonaws.com", 
    "ec2-54-235-143-131.compute-1.amazonaws.com", 
    "ec2-54-235-143-133.compute-1.amazonaws.com", 
    "ec2-54-235-143-162.compute-1.amazonaws.com", 
    "ec2-75-101-159-82.compute-1.amazonaws.com", 
    "ec2-54-225-88-116.compute-1.amazonaws.com", 
    "ec2-23-23-130-201.compute-1.amazonaws.com", 
    "ec2-23-23-169-133.compute-1.amazonaws.com", 
    "ec2-54-225-229-159.compute-1.amazonaws.com", 
    "ec2-107-22-234-92.compute-1.amazonaws.com", 
    "ec2-107-20-176-139.compute-1.amazonaws.com", 
    "dev11-20120311.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "us-east-1e": [
    "ec2-23-23-170-30.compute-1.amazonaws.com", 
    "production-db7.co735munpzcw.us-east-1.rds.amazonaws.com", 
    "production-readonly-db7.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "web-mktg-1": [
    "web-mktg-1.co735munpzcw.us-east-1.rds.amazonaws.com"
  ], 
  "web1.axialmarket.com": [
    "ec2-75-101-157-248.compute-1.amazonaws.com"
  ], 
  "web2.axialmarket.com": [
    "ec2-75-101-159-82.compute-1.amazonaws.com"
  ], 
  "willnew.axialmarket.com": [
    "ec2-107-22-234-22.compute-1.amazonaws.com"
  ], 
  "worker1new.axialmarket.com": [
    "ec2-54-235-143-133.compute-1.amazonaws.com"
  ], 
  "worker1newdev.axialmarket.com": [
    "ec2-107-22-249-212.compute-1.amazonaws.com"
  ], 
  "worker2new.axialmarket.com": [
    "ec2-54-235-143-134.compute-1.amazonaws.com"
  ], 
  "www-test.axialmarket.com": [
    "ec2-54-234-233-19.compute-1.amazonaws.com"
  ],
  '_meta': {
    'hostvars': {}
  }
}

host_vars = {
    
}

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--list', action='store_true', dest='list')
    parser.add_option('--host', dest='hostname', default='')
    options, args = parser.parse_args()
    if options.list:
        print json.dumps(inv_list, indent=4)
    elif options.hostname:
        print json.dumps(host_vars, indent=4)
    else:
        print json.dumps({}, indent=4)


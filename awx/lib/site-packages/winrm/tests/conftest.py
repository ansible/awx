import os
import json
import uuid
import xmltodict
from pytest import skip, fixture
from mock import patch


open_shell_request = """\
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <env:Header>
    <a:To>http://windows-host:5985/wsman</a:To>
    <a:ReplyTo>
      <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
    <a:MessageID>uuid:11111111-1111-1111-1111-111111111111</a:MessageID>
    <w:Locale mustUnderstand="false" xml:lang="en-US" />
    <p:DataLocale mustUnderstand="false" xml:lang="en-US" />
    <w:OperationTimeout>PT60S</w:OperationTimeout>
    <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
    <a:Action mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/transfer/Create</a:Action>
    <w:OptionSet>
      <w:Option Name="WINRS_NOPROFILE">FALSE</w:Option>
      <w:Option Name="WINRS_CODEPAGE">437</w:Option>
    </w:OptionSet>
  </env:Header>
  <env:Body>
    <rsp:Shell>
      <rsp:InputStreams>stdin</rsp:InputStreams>
      <rsp:OutputStreams>stdout stderr</rsp:OutputStreams>
    </rsp:Shell>
  </env:Body>
</env:Envelope>"""

open_shell_response = """\
<?xml version="1.0" ?>
<s:Envelope xml:lang="en-US" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer">
    <s:Header>
        <a:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/CreateResponse</a:Action>
        <a:MessageID>uuid:11111111-1111-1111-1111-111111111112</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:11111111-1111-1111-1111-111111111111</a:RelatesTo>
    </s:Header>
    <s:Body>
        <x:ResourceCreated>
            <a:Address>http://windows-host:5985/wsman</a:Address>
            <a:ReferenceParameters>
                <w:ResourceURI>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
                <w:SelectorSet>
                    <w:Selector Name="ShellId">11111111-1111-1111-1111-111111111113</w:Selector>
                </w:SelectorSet>
            </a:ReferenceParameters>
        </x:ResourceCreated>
    </s:Body>
</s:Envelope>"""

close_shell_request = """\
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <env:Header>
    <a:To>http://windows-host:5985/wsman</a:To>
    <a:ReplyTo>
      <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
    <a:MessageID>uuid:11111111-1111-1111-1111-111111111111</a:MessageID>
    <w:Locale mustUnderstand="false" xml:lang="en-US" />
    <p:DataLocale mustUnderstand="false" xml:lang="en-US" />
    <w:OperationTimeout>PT60S</w:OperationTimeout>
    <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
    <a:Action mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/transfer/Delete</a:Action>
    <w:SelectorSet>
      <w:Selector Name="ShellId">11111111-1111-1111-1111-111111111113</w:Selector>
    </w:SelectorSet>
  </env:Header>
  <env:Body>
  </env:Body>
</env:Envelope>"""

close_shell_response = """\
<?xml version="1.0" ?>
<s:Envelope xml:lang="en-US" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/DeleteResponse</a:Action>
        <a:MessageID>uuid:11111111-1111-1111-1111-111111111112</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:11111111-1111-1111-1111-111111111111</a:RelatesTo>
    </s:Header>
    <s:Body/>
</s:Envelope>
"""

run_cmd_with_args_request = """\
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <env:Header>
    <a:To>http://windows-host:5985/wsman</a:To>
    <a:ReplyTo>
      <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
    <a:MessageID>uuid:11111111-1111-1111-1111-111111111111</a:MessageID>
    <w:Locale mustUnderstand="false" xml:lang="en-US" />
    <p:DataLocale mustUnderstand="false" xml:lang="en-US" />
    <w:OperationTimeout>PT60S</w:OperationTimeout>
    <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
    <a:Action mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Command</a:Action>
    <w:SelectorSet>
      <w:Selector Name="ShellId">11111111-1111-1111-1111-111111111113</w:Selector>
    </w:SelectorSet>
    <w:OptionSet>
      <w:Option Name="WINRS_CONSOLEMODE_STDIN">TRUE</w:Option>
      <w:Option Name="WINRS_SKIP_CMD_SHELL">FALSE</w:Option>
    </w:OptionSet>
  </env:Header>
  <env:Body>
    <rsp:CommandLine>
      <rsp:Command>ipconfig</rsp:Command>
      <rsp:Arguments>/all</rsp:Arguments>
    </rsp:CommandLine>
  </env:Body>
</env:Envelope>"""

run_cmd_wo_args_request = """\
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <env:Header>
    <a:To>http://windows-host:5985/wsman</a:To>
    <a:ReplyTo>
      <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
    <a:MessageID>uuid:11111111-1111-1111-1111-111111111111</a:MessageID>
    <w:Locale mustUnderstand="false" xml:lang="en-US" />
    <p:DataLocale mustUnderstand="false" xml:lang="en-US" />
    <w:OperationTimeout>PT60S</w:OperationTimeout>
    <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
    <a:Action mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Command</a:Action>
    <w:SelectorSet>
      <w:Selector Name="ShellId">11111111-1111-1111-1111-111111111113</w:Selector>
    </w:SelectorSet>
    <w:OptionSet>
      <w:Option Name="WINRS_CONSOLEMODE_STDIN">TRUE</w:Option>
      <w:Option Name="WINRS_SKIP_CMD_SHELL">FALSE</w:Option>
    </w:OptionSet>
  </env:Header>
  <env:Body>
    <rsp:CommandLine>
      <rsp:Command>hostname</rsp:Command>
    </rsp:CommandLine>
  </env:Body>
</env:Envelope>"""

run_cmd_response = """\
<?xml version="1.0" ?>
<s:Envelope xml:lang="en-US" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer">
    <s:Header>
        <a:Action>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandResponse</a:Action>
        <a:MessageID>uuid:11111111-1111-1111-1111-111111111112</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:11111111-1111-1111-1111-111111111111</a:RelatesTo>
    </s:Header>
    <s:Body>
        <rsp:CommandResponse>
            <rsp:CommandId>11111111-1111-1111-1111-111111111114</rsp:CommandId>
        </rsp:CommandResponse>
    </s:Body>
</s:Envelope>"""

cleanup_cmd_request = """\
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <env:Header>
    <a:To>http://windows-host:5985/wsman</a:To>
    <a:ReplyTo>
      <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
    <a:MessageID>uuid:11111111-1111-1111-1111-111111111111</a:MessageID>
    <w:Locale mustUnderstand="false" xml:lang="en-US" />
    <p:DataLocale mustUnderstand="false" xml:lang="en-US" />
    <w:OperationTimeout>PT60S</w:OperationTimeout>
    <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
    <a:Action mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Signal</a:Action>
    <w:SelectorSet>
      <w:Selector Name="ShellId">11111111-1111-1111-1111-111111111113</w:Selector>
    </w:SelectorSet>
  </env:Header>
  <env:Body>
    <rsp:Signal CommandId="11111111-1111-1111-1111-111111111114">
      <rsp:Code>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/signal/terminate</rsp:Code>
    </rsp:Signal>
  </env:Body>
</env:Envelope>"""

cleanup_cmd_response = """\
<?xml version="1.0" ?>
<s:Envelope xml:lang="en-US" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer">
    <s:Header>
        <a:Action>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/SignalResponse</a:Action>
        <a:MessageID>uuid:11111111-1111-1111-1111-111111111112</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:11111111-1111-1111-1111-111111111111</a:RelatesTo>
    </s:Header>
    <s:Body>
        <rsp:SignalResponse/>
    </s:Body>
</s:Envelope>"""

get_cmd_output_request = """\
<?xml version="1.0" encoding="utf-8"?>
<env:Envelope xmlns:x="http://schemas.xmlsoap.org/ws/2004/09/transfer" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:cfg="http://schemas.microsoft.com/wbem/wsman/1/config" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:n="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:b="http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <env:Header>
    <a:To>http://windows-host:5985/wsman</a:To>
    <a:ReplyTo>
      <a:Address mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <w:MaxEnvelopeSize mustUnderstand="true">153600</w:MaxEnvelopeSize>
    <a:MessageID>uuid:11111111-1111-1111-1111-111111111111</a:MessageID>
    <w:Locale mustUnderstand="false" xml:lang="en-US" />
    <p:DataLocale mustUnderstand="false" xml:lang="en-US" />
    <w:OperationTimeout>PT60S</w:OperationTimeout>
    <w:ResourceURI mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd</w:ResourceURI>
    <a:Action mustUnderstand="true">http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive</a:Action>
    <w:SelectorSet>
      <w:Selector Name="ShellId">11111111-1111-1111-1111-111111111113</w:Selector>
    </w:SelectorSet>
  </env:Header>
  <env:Body>
    <rsp:Receive>
      <rsp:DesiredStream CommandId="11111111-1111-1111-1111-111111111114">stdout stderr</rsp:DesiredStream>
    </rsp:Receive>
  </env:Body>
</env:Envelope>"""

get_cmd_output_response = """\
<?xml version="1.0" ?>
<s:Envelope xml:lang="en-US" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:p="http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd" xmlns:rsp="http://schemas.microsoft.com/wbem/wsman/1/windows/shell" xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <a:Action>http://schemas.microsoft.com/wbem/wsman/1/windows/shell/ReceiveResponse</a:Action>
        <a:MessageID>uuid:11111111-1111-1111-1111-111111111112</a:MessageID>
        <a:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:To>
        <a:RelatesTo>uuid:11111111-1111-1111-1111-111111111111</a:RelatesTo>
    </s:Header>
    <s:Body>
        <rsp:ReceiveResponse>
            <rsp:Stream CommandId="11111111-1111-1111-1111-111111111114" Name="stdout">DQpXaW5kb3dzIElQIENvbmZpZ3VyYXRpb24NCg0K</rsp:Stream>
            <rsp:Stream CommandId="11111111-1111-1111-1111-111111111114" Name="stdout">ICAgSG9zdCBOYW1lIC4gLiAuIC4gLiAuIC4gLiAuIC4gLiAuIDogV0lORE9XUy1IT1NUCiAgIFByaW1hcnkgRG5zIFN1ZmZpeCAgLiAuIC4gLiAuIC4gLiA6IAogICBOb2RlIFR5cGUgLiAuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBIeWJyaWQKICAgSVAgUm91dGluZyBFbmFibGVkLiAuIC4gLiAuIC4gLiAuIDogTm8KICAgV0lOUyBQcm94eSBFbmFibGVkLiAuIC4gLiAuIC4gLiAuIDogTm8KCkV0aGVybmV0IGFkYXB0ZXIgTG9jYWwgQXJlYSBDb25uZWN0aW9uOgoKICAgQ29ubmVjdGlvbi1zcGVjaWZpYyBETlMgU3VmZml4ICAuIDogCiAgIERlc2NyaXB0aW9uIC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IEludGVsKFIpIDgyNTY3Vi0yIEdpZ2FiaXQgTmV0d29yayBDb25uZWN0aW9uCiAgIFBoeXNpY2FsIEFkZHJlc3MuIC4gLiAuIC4gLiAuIC4gLiA6IEY4LTBGLTQxLTE2LTg4LUU4CiAgIERIQ1AgRW5hYmxlZC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IE5vCiAgIEF1dG9jb25maWd1cmF0aW9uIEVuYWJsZWQgLiAuIC4gLiA6IFllcwogICBMaW5rLWxvY2FsIElQdjYgQWRkcmVzcyAuIC4gLiAuIC4gOiBmZTgwOjphOTkwOjM1ZTM6YTZhYjpmYzE1JTEwKFByZWZlcnJlZCkgCiAgIElQdjQgQWRkcmVzcy4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IDE3My4xODUuMTUzLjkzKFByZWZlcnJlZCkgCiAgIFN1Ym5ldCBNYXNrIC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IDI1NS4yNTUuMjU1LjI0OAogICBEZWZhdWx0IEdhdGV3YXkgLiAuIC4gLiAuIC4gLiAuIC4gOiAxNzMuMTg1LjE1My44OQogICBESENQdjYgSUFJRCAuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiAyNTExMzc4NTcKICAgREhDUHY2IENsaWVudCBEVUlELiAuIC4gLiAuIC4gLiAuIDogMDAtMDEtMDAtMDEtMTYtM0ItM0YtQzItRjgtMEYtNDEtMTYtODgtRTgKICAgRE5TIFNlcnZlcnMgLiAuIC4gLiAuIC4gLiAuIC4gLiAuIDogMjA3LjkxLjUuMzIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgMjA4LjY3LjIyMi4yMjIKICAgTmV0QklPUyBvdmVyIFRjcGlwLiAuIC4gLiAuIC4gLiAuIDogRW5hYmxlZAoKRXRoZXJuZXQgYWRhcHRlciBMb2NhbCBBcmVhIENvbm5lY3Rpb24qIDk6CgogICBNZWRpYSBTdGF0ZSAuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBNZWRpYSBkaXNjb25uZWN0ZWQKICAgQ29ubmVjdGlvbi1zcGVjaWZpYyBETlMgU3VmZml4ICAuIDogCiAgIERlc2NyaXB0aW9uIC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IEp1bmlwZXIgTmV0d29yayBDb25uZWN0IFZpcnR1YWwgQWRhcHRlcgogICBQaHlzaWNhbCBBZGRyZXNzLiAuIC4gLiAuIC4gLiAuIC4gOiAwMC1GRi1BMC04My00OC0wNAogICBESENQIEVuYWJsZWQuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBZZXMKICAgQXV0b2NvbmZpZ3VyYXRpb24gRW5hYmxlZCAuIC4gLiAuIDogWWVzCgpUdW5uZWwgYWRhcHRlciBpc2F0YXAue0FBNDI2QjM3LTM2OTUtNEVCOC05OTBGLTRDRkFDODQ1RkQxN306CgogICBNZWRpYSBTdGF0ZSAuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBNZWRpYSBkaXNjb25uZWN0ZWQKICAgQ29ubmVjdGlvbi1zcGVjaWZpYyBETlMgU3VmZml4ICAuIDogCiAgIERlc2NyaXB0aW9uIC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IE1pY3Jvc29mdCBJU0FUQVAgQWRhcHRlcgogICBQaHlzaWNhbCBBZGRyZXNzLiAuIC4gLiAuIC4gLiAuIC4gOiAwMC0wMC0wMC0wMC0wMC0wMC0wMC1FMAogICBESENQIEVuYWJsZWQuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBObwogICBBdXRvY29uZmlndXJhdGlvbiBFbmFibGVkIC4gLiAuIC4gOiBZZXMKClR1bm5lbCBhZGFwdGVyIFRlcmVkbyBUdW5uZWxpbmcgUHNldWRvLUludGVyZmFjZToKCiAgIENvbm5lY3Rpb24tc3BlY2lmaWMgRE5TIFN1ZmZpeCAgLiA6IAogICBEZXNjcmlwdGlvbiAuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBUZXJlZG8gVHVubmVsaW5nIFBzZXVkby1JbnRlcmZhY2UKICAgUGh5c2ljYWwgQWRkcmVzcy4gLiAuIC4gLiAuIC4gLiAuIDogMDAtMDAtMDAtMDAtMDAtMDAtMDAtRTAKICAgREhDUCBFbmFibGVkLiAuIC4gLiAuIC4gLiAuIC4gLiAuIDogTm8KICAgQXV0b2NvbmZpZ3VyYXRpb24gRW5hYmxlZCAuIC4gLiAuIDogWWVzCiAgIElQdjYgQWRkcmVzcy4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IDIwMDE6MDo5ZDM4Ojk1M2M6MmNlZjo3ZmM6NTI0Njo2NmEyKFByZWZlcnJlZCkgCiAgIExpbmstbG9jYWwgSVB2NiBBZGRyZXNzIC4gLiAuIC4gLiA6IGZlODA6OjJjZWY6N2ZjOjUyNDY6NjZhMiUxMyhQcmVmZXJyZWQpIAogICBEZWZhdWx0IEdhdGV3YXkgLiAuIC4gLiAuIC4gLiAuIC4gOiAKICAgTmV0QklPUyBvdmVyIFRjcGlwLiAuIC4gLiAuIC4gLiAuIDogRGlzYWJsZWQKClR1bm5lbCBhZGFwdGVyIDZUTzQgQWRhcHRlcjoKCiAgIENvbm5lY3Rpb24tc3BlY2lmaWMgRE5TIFN1ZmZpeCAgLiA6IAogICBEZXNjcmlwdGlvbiAuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiBNaWNyb3NvZnQgNnRvNCBBZGFwdGVyICMyCiAgIFBoeXNpY2FsIEFkZHJlc3MuIC4gLiAuIC4gLiAuIC4gLiA6IDAwLTAwLTAwLTAwLTAwLTAwLTAwLUUwCiAgIERIQ1AgRW5hYmxlZC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IE5vCiAgIEF1dG9jb25maWd1cmF0aW9uIEVuYWJsZWQgLiAuIC4gLiA6IFllcwogICBJUHY2IEFkZHJlc3MuIC4gLiAuIC4gLiAuIC4gLiAuIC4gOiAyMDAyOmFkYjk6OTk1ZDo6YWRiOTo5OTVkKFByZWZlcnJlZCkgCiAgIERlZmF1bHQgR2F0ZXdheSAuIC4gLiAuIC4gLiAuIC4gLiA6IDIwMDI6YzA1ODo2MzAxOjpjMDU4OjYzMDEKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgMjAwMjpjMDU4OjYzMDE6OjEKICAgRE5TIFNlcnZlcnMgLiAuIC4gLiAuIC4gLiAuIC4gLiAuIDogMjA3LjkxLjUuMzIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgMjA4LjY3LjIyMi4yMjIKICAgTmV0QklPUyBvdmVyIFRjcGlwLiAuIC4gLiAuIC4gLiAuIDogRGlzYWJsZWQKClR1bm5lbCBhZGFwdGVyIGlzYXRhcC57QkExNjBGQzUtNzAyOC00QjFGLUEwNEItMUFDODAyQjBGRjVBfToKCiAgIE1lZGlhIFN0YXRlIC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IE1lZGlhIGRpc2Nvbm5lY3RlZAogICBDb25uZWN0aW9uLXNwZWNpZmljIEROUyBTdWZmaXggIC4gOiAKICAgRGVzY3JpcHRpb24gLiAuIC4gLiAuIC4gLiAuIC4gLiAuIDogTWljcm9zb2Z0IElTQVRBUCBBZGFwdGVyICMyCiAgIFBoeXNpY2FsIEFkZHJlc3MuIC4gLiAuIC4gLiAuIC4gLiA6IDAwLTAwLTAwLTAwLTAwLTAwLTAwLUUwCiAgIERIQ1AgRW5hYmxlZC4gLiAuIC4gLiAuIC4gLiAuIC4gLiA6IE5vCiAgIEF1dG9jb25maWd1cmF0aW9uIEVuYWJsZWQgLiAuIC4gLiA6IFllcwo=</rsp:Stream>
            <rsp:Stream CommandId="11111111-1111-1111-1111-111111111114" End="true" Name="stdout"/>
            <rsp:Stream CommandId="11111111-1111-1111-1111-111111111114" End="true" Name="stderr"/>
            <rsp:CommandState CommandId="11111111-1111-1111-1111-111111111114" State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Done">
                <rsp:ExitCode>0</rsp:ExitCode>
            </rsp:CommandState>
        </rsp:ReceiveResponse>
    </s:Body>
</s:Envelope>"""


def sort_dict(ordered_dict):
    items = sorted(ordered_dict.items(), key=lambda x: x[0])
    ordered_dict.clear()
    for key, value in items:
        if isinstance(value, dict):
            sort_dict(value)
        ordered_dict[key] = value


def xml_str_compare(first, second):
    first_dict = xmltodict.parse(first)
    second_dict = xmltodict.parse(second)
    sort_dict(first_dict)
    sort_dict(second_dict)
    return first_dict == second_dict


class TransportStub(object):
    def send_message(self, message):
        if xml_str_compare(message, open_shell_request):
            return open_shell_response
        elif xml_str_compare(message, close_shell_request):
            return close_shell_response
        elif xml_str_compare(
                message, run_cmd_with_args_request) or xml_str_compare(
                message, run_cmd_wo_args_request):
            return run_cmd_response
        elif xml_str_compare(message, cleanup_cmd_request):
            return cleanup_cmd_response
        elif xml_str_compare(message, get_cmd_output_request):
            return get_cmd_output_response
        else:
            raise Exception('Message was not expected')


@fixture(scope='module')
def protocol_fake(request):
    uuid4_patcher = patch('uuid.uuid4')
    uuid4_mock = uuid4_patcher.start()
    uuid4_mock.return_value = uuid.UUID(
        '11111111-1111-1111-1111-111111111111')

    from winrm.protocol import Protocol

    protocol_fake = Protocol(
        endpoint='http://windows-host:5985/wsman',
        transport='plaintext',
        username='john.smith',
        password='secret')

    protocol_fake.transport = TransportStub()

    def uuid4_patch_stop():
        uuid4_patcher.stop()

    request.addfinalizer(uuid4_patch_stop)
    return protocol_fake


@fixture(scope='module')
def protocol_real():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.isfile(config_path):
        # TODO consider replace json with yaml for integration test settings
        # TODO json does not support comments
        settings = json.load(open(config_path))

        from winrm.protocol import Protocol
        protocol = Protocol(**settings)
        return protocol
    else:
        skip('config.json was not found. Integration tests will be skipped')
<?xml version="1.0" encoding="UTF-8"?>
<!--
The MIT License (MIT)

Copyright (c) 2018, Falco Nikolas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
-->
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema"
	xmlns:xunit="http://www.xunit.org" xmlns:math="http://exslt.org/math" extension-element-prefixes="math">
	<xsl:output method="xml" indent="yes" encoding="UTF-8" cdata-section-elements="system-out system-err failure error" />
	<xsl:decimal-format decimal-separator="." grouping-separator="," />

	<xsl:function name="xunit:junit-time" as="xs:string">
		<xsl:param name="value" as="xs:anyAtomicType?" />

		<xsl:variable name="time" as="xs:double">
			<xsl:choose>
				<xsl:when test="$value instance of xs:double">
					<xsl:value-of select="$value" />
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="translate(string(xunit:if-empty($value, 0)), ',', '.')" />
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:value-of select="format-number($time, '0.000')" />
	</xsl:function>

	<xsl:function name="xunit:if-empty" as="xs:string">
		<xsl:param name="value" as="xs:anyAtomicType?" />
		<xsl:param name="default" as="xs:anyAtomicType" />
		<xsl:value-of select="if (string($value) != '') then string($value) else $default" />
	</xsl:function>

	<xsl:function name="xunit:is-empty" as="xs:boolean">
		<xsl:param name="value" as="xs:string?" />
		<xsl:value-of select="string($value) != ''" />
	</xsl:function>

	<xsl:template match="/testsuites">
		<testsuites>
			<xsl:apply-templates select="node() except (system-err | system-out | properties)" />
		</testsuites>
	</xsl:template>

	<xsl:key name="suiteName" match="testsuite" use="xunit:if-empty(@name, @package)" />

	<xsl:template match="//testsuite">
		<xsl:element name="testsuite">
			<xsl:attribute name="name" select="xunit:if-empty(@name, 0)" />
			<xsl:attribute name="time" select="xunit:junit-time(xunit:if-empty(@time, 0))" />
			<xsl:attribute name="tests" select="count(current()//testcase)" />
			<xsl:attribute name="failures" select="count(current()//testcase/failure[1])" />
			<xsl:attribute name="errors" select="count(current()//testcase/error[1])" />
			<xsl:attribute name="skipped" select="count(current()//testcase/skipped[1])" />
			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

	<xsl:template match="//testcase">
		<xsl:element name="testcase">
			<xsl:attribute name="name" select="xunit:if-empty(@name, 'no name')" />
			<xsl:if test="@time">
				<xsl:attribute name="time" select="xunit:junit-time(xunit:if-empty(@time, 0))" />
			</xsl:if>
			<xsl:if test="@classname">
				<xsl:attribute name="classname" select="@classname" />
			</xsl:if>
			<xsl:if test="@group">
				<xsl:attribute name="group" select="@group" />
			</xsl:if>

			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

	<xsl:template match="//skipped">
		<xsl:element name="skipped">
			<xsl:if test="@message">
				<xsl:attribute name="message" select="@message" />
			</xsl:if>
		</xsl:element>
	</xsl:template>

	<xsl:template match="//error[1]">
		<xsl:element name="error">
			<xsl:if test="@type">
				<xsl:attribute name="type" select="@type" />
			</xsl:if>
			<xsl:if test="@message">
				<xsl:attribute name="message" select="@message" />
			</xsl:if>
            <xsl:value-of select="text()"/>
		</xsl:element>
	</xsl:template>

    <xsl:template match="//failure[1]">
        <xsl:element name="failure">
            <xsl:if test="@type">
                <xsl:attribute name="type" select="@type" />
            </xsl:if>
            <xsl:if test="@message">
                <xsl:attribute name="message" select="@message" />
            </xsl:if>
            <xsl:value-of select="text()"/>
        </xsl:element>
    </xsl:template>

	<xsl:template match="//system-err">
		<xsl:element name="system-err">
            <xsl:value-of select="text()" />
        </xsl:element>
	</xsl:template>

	<xsl:template match="//system-out">
		<xsl:element name="system-out">
            <xsl:value-of select="text()" />
        </xsl:element>
	</xsl:template>

    <xsl:template match="//properties">
        <xsl:element name="properties">
            <xsl:for-each select="property">
                <xsl:if test="@name">
                    <xsl:element name="property">
                        <xsl:attribute name="name" select="@name" />
                        <xsl:attribute name="value" select="@value" />
                    </xsl:element>
                </xsl:if>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>

</xsl:stylesheet>
---
#
# By default, content added below the "---" mark will appear in the home page
# between the top bar and the list of recent posts.
# To change the home page layout, edit the _layouts/home.html file.
# See: https://jekyllrb.com/docs/themes/#overriding-theme-defaults
#
layout: home
---
<table>
        <tr>
        <th colspan="5" style="text-align: center;">Accessibility</th>
        </tr>
        <tr>
            <th colspan="1" style="text-align: center;">Metric</th>
            <th colspan="1" style="text-align: center;">Ref</th>
        </tr>
        <tr>
            <th colspan="5" style="text-align: center;">Availability</th>
        </tr>
        <tr>
            <td rowspan="8">Accessibility of the SPARQL endpoint</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>Checking whether the server responds to a SPARQL query</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/availability#accessibility-of-the-sparql-endpoint" target="_blank">Availability/SPARQL-endpoint</a>
            </td>
        </tr>
        <tr>
            <td rowspan="3">Output</td>
            <td>0</td>
            <td>The SPARQL endpoint is offline.</td>
        </tr>
        <tr>
            <td>1</td>
            <td>The SPARQL endpoint is online.</td>
        </tr>
        <tr>
            <td>-1</td>
            <td>The SPARQL endpoint is missing.</td>
        </tr>
        <tr></tr><tr></tr>
        <tr>
            <td rowspan="8">Accessibility of the RDF dump</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>Checking whether an RDF dump is provided and can be downloaded</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata, (working) SPARQL endpoint, VoID file</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/availability#accessibility-of-the-rdf-dump" target="_blank">Availability/RDF-Dump</a>
            </td>
        </tr>
        <tr>
            <td rowspan="3">Output</td>
            <td>0</td>
            <td>The RDF dump is offline.</td>
        </tr>
        <tr>
            <td>1</td>
            <td>The RDF dump is online.</td>
        </tr>
        <tr>
            <td>-1</td>
            <td>The RDF dump is missing.</td>
        </tr>
                <tr></tr><tr></tr>
        <tr>
            <td rowspan="8">Derefereaceability of the URI</td>
            <td rowspan="8"><a href="https://bit.ly/3R8tYBA" target="_blank">bit.ly/3R8tYBA</a></td>
            <td colspan="4"><i>HTTP URIs should be dereferenceable, i.e. HTTP clients should be able to retrieve the resources identified by the URI</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/availability#derefereaceability-of-the-uri" target="_blank">Availability/URIs-dereferenciability</a>
            </td>
        </tr>
        <tr>
            <td rowspan="1">Output</td>
            <td>[0,1]</td>
            <td>Best value: 1.</td>
        </tr>
        <tr></tr><tr></tr><tr></tr><tr></tr><tr><tr>
        <tr>
            <th colspan="5" style="text-align: center;">Licensing</th>
        </tr>
        <tr>
            <td rowspan="8">Machine-redeable license</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>detection of the indication of a license in the VoID description or in the dataset itself</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata, VoID file, (working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/licensing#machine-readable-license" target="_blank">Licensing/MR-License</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>The license can't be recovered</td>
        </tr>
        <tr>
            <td>1</td>
            <td>The license can be recovered</td>
        </tr>
        <tr></tr><tr></tr><tr></tr>
        <tr>
            <td rowspan="8">Human-readable license</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>Detection of a license in the documentation of the dataset</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/licensing#human-readable-license" target="_blank">Licensing/Human-readable</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>The license can't be recovered</td>
        </tr>
        <tr>
            <td>1</td>
            <td>The license can be recovered</td>
        </tr>
                <tr></tr><tr></tr><tr></tr>
    <tr>
            <th colspan="5" style="text-align: center;">Interlinking</th>
        </tr>
        <tr>
            <td rowspan="8">Degree of connection</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>detection of (a) interlinking degree, (b) clustering coefficient, (c) centrality, (d) open sameAs chains and (e) description
richness through sameAs by using network measures</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interlinking#degree-of-connection" target="_blank">Interlinking/Degr-Connection</a>
            </td>
        </tr>
        <tr>
            <td rowspan="1">Output</td>
            <td>N</td>
            <td>Number of external links</td>
        </tr>
        <tr></tr><tr></tr><tr></tr><tr>
        <tr>
            <td rowspan="8">Clustering coefficient</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">https://bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>(i) detection of (a) interlinking degree, (b) clustering coefficient, (c) centrality, (d) open sameAs chains and (e) description
richness through sameAs by using network measures</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interlinking#clustering-coefficient" target="_blank">Interlinking/Clustering-coefficient</a>
            </td>
        </tr>
        <tr>
            <td rowspan="1">Output</td>
            <td>[0,1] </td>
            <td>Best value: 1</td>
        </tr>
                <tr></tr><tr></tr><tr></tr><tr>
        <tr>
            <td rowspan="8">Centrality</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>(i) detection of (a) interlinking degree, (b) clustering coefficient, (c) centrality, (d) open sameAs chains and (e) description
richness through sameAs by using network measures</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interlinking#centrality" target="_blank">Interlinking/Centrality</a>
            </td>
        </tr>
        <tr>
            <td rowspan="1">Output</td>
            <td>[0,1] </td>
            <td>Best value: 1</td>
        </tr>
                <tr></tr><tr></tr><tr></tr>
                          <tr></tr><tr></tr><tr></tr><tr>
        <tr>
            <td rowspan="8">sameAs chains</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>(i) detection of (a) interlinking degree, (b) clustering coefficient, (c) centrality, (d) open sameAs chains and (e) description
richness through sameAs by using network measures</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interlinking#sameas-chains" target="_blank">Interlinking/sameAs</a>
            </td>
        </tr>
        <tr>
            <td rowspan="1">Output</td>
            <td>[0,1] </td>
            <td>Best value: 1</td>
        </tr>
                        <tr></tr><tr></tr><tr></tr>
                          <tr></tr><tr></tr><tr></tr><tr>
            <tr>
        <td rowspan="8">skos:*Match</td>
        <td rowspan="8"><a href="https://bit.ly/skosPr" target="_blank">bit.ly/skosPr</a></td>
        <td colspan="4"><i>skos:closeMatch | skos:exactMatch | skos:broadMatch | skos:narrowMatch | skos:relatedMatch</i></td>
    </tr>
    <tr>
        <td>Input</td>
        <td colspan="3">(working) SPARQL endpoint</td>
    </tr>
    <tr>
        <td rowspan="1">Algorithm</td>
        <td colspan="3">
        <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interlinking#skos-mapping-properties" target="_blank">Interlinking/skos:*Match</a>
        </td>
    </tr>
    <tr>
        <td rowspan="1">Output</td>
        <td>[0,1] </td>
        <td>Best value: 1</td>
    </tr>
                <tr></tr><tr></tr><tr></tr><tr></tr>
            <tr>
            <th colspan="5" style="text-align: center;">Security</th>
        </tr>
        <tr>
            <td rowspan="8">Access to data is secure</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>use of login credentials (or use of SSL or SSH)</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/security#access-to-data-is-secure" target="_blank">Security/Sec-acc</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>Authentication is required</td>
        </tr>
        <tr>
            <td>1</td>
            <td>No authentication required</td>
        </tr>
        <tr></tr><tr></tr><tr></tr><tr>
        <tr>
            <td rowspan="8">Access to data is secure</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>HTTPS support</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/security#use-https" target="_blank">Security/https</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>Does not use HTTPS</td>
        </tr>
        <tr>
            <td>1</td>
            <td>Use HTTPS</td>
        </tr>
        <tr><tr><tr></tr></tr></tr>
        <tr>
            <th colspan="5" style="text-align: center;">Performance</th>
        </tr>
        <tr>
            <td rowspan="8">Low latency</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>if an HTTP-request is not answered within an average time of one second, the latency of the data source is considered too low</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/performance#low-latency" target="_blank">Performance/Latency</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>1 if latency less than 1'' otherwise 1000/avg latency</td>
        </tr>
        <tr></tr><tr></tr><tr></tr><tr>
        <tr>
            <td rowspan="8">High Throughput</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>no. of answered HTTP-requests per second</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/performance#high-throughput" target="_blank">Performance/Throughput</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>1 if more than 5 requests otherwise num of fulfilled requests/200</td>
        </tr>
     <tr><tr><tr><tr></tr></tr></tr></tr>
     <tr>
        <th colspan="5" style="text-align: center;">Intrinsic</th>
        </tr>
         <tr>
            <th colspan="5" style="text-align: center;">Semantic Accuracy</th>
        </tr>
        <tr>
            <td rowspan="8">Empty annotation labels</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>labels, comments, notes which identifies triples whose property’s object value is empty string</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/semantic-accuracy##empty-annotation-labels" target="_blank">Accuracy/Empty-label</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
         <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">White space in annotation</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>presence of white space in labels</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/semantic-accuracy#white-space-in-annotation" target="_blank">Accuracy/Whitespace</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
         <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Datatype consistency</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>Incompatible with data type range</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/semantic-accuracy#datatype-consistency" target="_blank">Accuracy/Datatype</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Functional property violation</td>
            <td rowspan="8"><a href="https://bit.ly/3Rts9QV" target="_blank">bit.ly/3Rts9QV</a></td>
            <td colspan="4"><i>FP = 1 - num of triples of with inconsistent values for functional properties / num of triples</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/semantic-accuracy#functional-property-violation" target="_blank">Accuracy/FP</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
                <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Inverse functional violation</td>
            <td rowspan="8"><a href="https://bit.ly/3Rts9QV" target="_blank">bit.ly/3Rts9QV</a></td>
            <td colspan="4"><i>IFP = 1 - num of triples of with inconsistent values for functional properties / num of triples</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/semantic-accuracy#inverse-functional-property-violation" target="_blank">Accuracy/IFP</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
         <tr> <tr> <tr> <tr></tr> </tr> </tr> </tr>
 <tr>
            <th colspan="5" style="text-align: center;">Consistency</th>
        </tr>
        <tr>
            <td rowspan="8">Entities as members of disjoint classes</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>no. of entities described as members of disjoint classes / total no. of entities described in the dataset</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/consistency#entities-as-members-of-disjoint-classes" target="_blank">Consistency/Disjoint</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
         <tr> <tr> <tr> <tr></tr> </tr> </tr> </tr>
        <tr>
            <td rowspan="8">Misplaced classes or properties </td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>Detection of a URI defined as a class is used as a property or a URI defined as a property is used as a class</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/consistency#misplaced-class" target="_blank">Consistency/Misplaced</a>
            </td>
        </tr>
                <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
                <tr>
            <td rowspan="8">Use of members of deprecated classes or properties </td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>detection of use of OWL classes owl:DeprecatedClass and owl:DeprecatedProperty</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/consistency#use-of-members-of-deprecated-classes-or-properties" target="_blank">Consistency/Deprecated</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
                <tr>
            <td rowspan="8">Invalid usage of undefined classes and properties </td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>detection of classes and properties used without any formal definition</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/consistency#undefined-classes" target="_blank">Consistency/Undefined</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
                <tr>
            <td rowspan="8">Ontology hijacking </td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>detection of the redefinition by third parties of external classes/ properties such that reasoning over data using those external terms is affected</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/consistency#ontology-hijacking" target="_blank">Consistency/Hijacking</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
         <tr> <tr> <tr> <tr></tr> </tr> </tr> </tr>
 <tr>
            <th colspan="5" style="text-align: center;">Conciseness</th>
        </tr>
        <tr>
            <td rowspan="8">Intensional conciseness</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>number of unique attributes of a dataset in relation to the overall number of attributes in a target schema</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/conciseness#intensional-conciseness" target="_blank">Conciseness/Int-Conc</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr> <tr> <tr> <tr></tr> </tr> </tr> </tr>
        <tr>
            <td rowspan="8">Extensional conciseness</td>
            <td rowspan="8"><a href="https://bit.ly/4a4xRA6" target="_blank">bit.ly/4a4xRA6</a></td>
            <td colspan="4"><i>number of unique objects in relation to the overall number of object representations in the datase</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/conciseness#extensional-conciseness" target="_blank">Conciseness/Ext-Conc</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
     <tr>
        <th colspan="5" style="text-align: center;">Trust</th>
        </tr>
         <tr>
            <th colspan="5" style="text-align: center;">Reputation</th>
        </tr>
        <tr>
            <td rowspan="8">Reputation of the dataset </td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>analyzing page rank of the dataset</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/reputation#reputation-of-the-dataset" target="_blank">Reputation/PageRank</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
                 <tr>
            <th colspan="5" style="text-align: center;">Believability</th>
        </tr>
        <tr>
            <td rowspan="8">Meta-information about the identity of information provider</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>checking whether the provider/contributor is contained in a list of trusted providers</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/believability#meta-information-about-the-identity-of-information-provider" target="_blank">Believability/Meta-info</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
                 <tr>
            <th colspan="5" style="text-align: center;">Verifiability</th>
        </tr>
        <tr>
            <td rowspan="8">Verifying publisher information</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>stating the author and his contributors, the publisher of the data and its sources</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint, VoID file</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/verifiability#verifying-publisher-information" target="_blank">Verifiability/Publisher-info</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>If no information are provided</td>
        </tr>
        <tr>
            <td>1</td>
            <td>1 if all information are provided</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Verifying authenticity of the dataset</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>whether the dataset uses a provenance vocabulary</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint, VoID file</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/verifiability#verifying-authenticity-of-the-dataset" target="_blank">Verifiability/Vocabs</a>
            </td>
        </tr>
        <tr>
            <td rowspan>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Verifying usage of digital signatures</td>
            <td rowspan="8"><a href="https://bit.ly/41dNO2P" target="_blank">bit.ly/41dNO2P</a></td>
            <td colspan="4"><i>signing a document containing an RDF serialisation or signing an RDF graph</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/verifiability#verifying-usage-of-digital-signatures" target="_blank">Verifiability/Publisher-info</a>
            </td>
        </tr>
<tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>0 if the signature is not present</td>
        </tr>
        <tr>
            <td>1</td>
            <td>0 if the signature is present</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
     <tr>
        <th colspan="5" style="text-align: center;">Dataset dynamicity</th>
        </tr>
         <tr>
            <th colspan="5" style="text-align: center;">Currency</th>
        </tr>
        <tr>
            <td rowspan="8">Time since the last modification</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>currency only measures the time since the last modification</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint, VoID file</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/currency#time-since-last-modification" target="_blank">Currency/LastModification</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the modification date is correctly retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>otherwise</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Specification of the modification date of statements</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>use of dates as the point in time of the last verification of a statement represented by dcterms:modifieds</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint, VoID file</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/currency#specification-of-the-modification-date-of-statements" target="_blank">Currency/Modification</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the modification date can't be retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the modification date is correctly retrieved</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Age of data</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>current time - created time</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint, VoID file</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/currency#age-of-data" target="_blank">Currency/AgeOfData</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the creation date can't be recovered</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the creation date is correctly recovered</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
<tr>
            <th colspan="5" style="text-align: center;">Timeliness</th>
        </tr>
        <tr>
            <td rowspan="8">Stating the recency and frequency of data validation</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>it corresponds to the "stating the [...] frequency of data validation"</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/timeliness#stating-the-recency-and-frequency-of-data-validation" target="_blank">Timeliness/Frequency</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the frequency can't be retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the frequency is correctly retrieved</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
     <tr>
        <th colspan="5" style="text-align: center;">Contextual</th>
        </tr>
         <tr>
            <th colspan="5" style="text-align: center;">Completeness</th>
        </tr>
        <tr>
            <td rowspan="8">Interlinking completeness</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>degree to which interlinks are not missing </i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/completeness#interlinking-completeness" target="_blank">Completeness/Interl</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
             <tr>
            <th colspan="5" style="text-align: center;">Amount of data</th>
        </tr>
        <tr>
            <td rowspan="8">Number of triples</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>Number of triples</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata, (working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/amount_of_data#number-of-triples" target="_blank">AmountOfData/Triples</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the number of triples can't be retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the number of triples can be retrieved</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Level of detail</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>Number of properties</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">VoID file, (working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/amount_of_data#level-of-detail" target="_blank">AmountOfData/Property</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the number of property can't be retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the number of property can be retrieved</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Scope</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>Number of entities</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">VoID file, (working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/amount_of_data#scope" target="_blank">AmountOfData/Entities</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the number of entity can't be retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the number of entity can be retrieved</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
     <tr>
        <th colspan="5" style="text-align: center;">Representational</th>
        </tr>
         <tr>
            <th colspan="5" style="text-align: center;">Representational-conciseness</th>
        </tr>
        <tr>
            <td rowspan="8">Keeping URI short</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV" target="_blank">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>detection of long URIs or those that contain query param-eters </i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/representational_conciseness#keeping-uri-short">Rep-Conc/ShortUri</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
         <tr>
            <th colspan="5" style="text-align: center;">Interoperability</th>
        </tr>
        <tr>
            <td rowspan="8">Re-use of existing vocabularies</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>usage of established vocabularies</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interoperability#re-use-of-existing-vocabularies">Rep-Cons/NewVocabs</a>
            </td>
        </tr>
<tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if there are new vocabularies</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if all used vocabularies are already defined</td>
        </tr>
        <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Re-use of existing terms</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>detection of whether existing terms from all relevant vo-cabularies for that particular domain have been reuse</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interoperability#re-use-of-existing-terms">Rep-Cons/NewTerms</a>
            </td>
        </tr>
<tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if there are new terms</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if all used terms are already defined</td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
         <tr>
            <th colspan="5" style="text-align: center;">Understandability</th>
        </tr>
        <tr>
            <td rowspan="8">Human-readable labelling of classes, properties and entities by providing rdfs:label</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>no. of entities described by stating an rdfs:label or rdfs:comment in the dataset / total no. of entities described in the data</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/understandability#human-readable-labelling-of-classes-properties-and-entities-by-providing-rdfslabel">Under/Label</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Indication of metadata about a dataset</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>checking for the presence of the title, content and URI of the dataset</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/understandability#indication-of-metadata-about-a-dataset">Under/info</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if there aren't all information</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if there are all information required </td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Indication of an exemplary SPARQL query</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>detecting whether examples of SPARQL queries are provided</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">Metadata</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/understandability#indication-of-an-exemplary-sparql-query">Under/example</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if there is no example</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if at least one example is present</td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Indication of a regular expression that matches the URIs of a dataset</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>detecting whether a regular expression that matches the
URIs is present </i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">VoID file, (working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/understandability#indication-of-a-regular-expression-that-matches-the-uris-of-a-dataset">Under/regex</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the regex is not indicated</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if the regex is indicated</td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Indication of the vocabularies used in the dataset</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>checking whether a list of vocabularies used in the dataset is provided</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/understandability#indication-of-the-vocabularies-used-in-the-dataset">Under/Vocabs</a>
            </td>
        </tr>
        <tr>
            <td rowspan>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
         <tr>
            <th colspan="5" style="text-align: center;">Interpretability</th>
        </tr>
        <tr>
            <td rowspan="8">No misinterpretation of missing values</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>detecting the use of blank nodes</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interpretability#no-misinterpretation-of-missing-values">Under/Bns</a>
            </td>
        </tr>
        <tr>
            <td>Output</td>
            <td>[0,1]</td>
            <td>Best value: 1</td>
        </tr>
 <tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Atypical use of collections containers and reification</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>detection of the non-standard usage of collections, containers and reification</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/interpretability#atypical-use-of-collections-containers-and-reification">Under/Rdf</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if RDF structures are used.</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if RDF structures aren't used.</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
         <tr>
            <th colspan="5" style="text-align: center;">Versatility</th>
        </tr>
        <tr>
            <td rowspan="8">Usage of multiple languages</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>checking whether data is available in different languages</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/versatility#usage-of-multiple-languages">Versatility/Languages</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if no lang tag is retrieved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if at least a lang tag is retrieved</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Different serialization formats</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>checking whether data is available in different serialization formats</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/versatility#different-serialization-formats">Versatility/Serialization</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if no serialization format is provided</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if at least a serialization format is provided</td>
        </tr>
<tr><tr><tr><tr></tr></tr></tr></tr>
        <tr>
            <td rowspan="8">Accessing of data in different ways</td>
            <td rowspan="8"><a href="https://bit.ly/3RtIeWV">bit.ly/3RtIeWV</a></td>
            <td colspan="4"><i>cchecking whether the data is available as a SPARQL endpoint and is available for download as an RDF dump</i></td>
        </tr>
        <tr>
            <td>Input</td>
            <td colspan="3">(working) SPARQL endpoint</td>
        </tr>
        <tr>
            <td rowspan="1">Algorithm</td>
            <td colspan="3">
            <a href="https://isislab-unisa.github.io/KGHeartBeat/quality_dimensions/versatility#accessing-of-data-in-different-ways">Versatility/Access</a>
            </td>
        </tr>
        <tr>
            <td rowspan="2">Output</td>
            <td>0</td>
            <td>if the sparql endpoint or rdf dump is not online</td>
        </tr>
        <tr>
            <td>1</td>
            <td>if SPARQL endpoint and RDF dump are online.</td>
        </tr>
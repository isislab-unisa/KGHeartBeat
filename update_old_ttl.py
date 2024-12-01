from rdflib import URIRef, Literal, XSD, Graph
from pathlib import Path
import os
from datetime import datetime
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS, FOAF, PROV

here = os.path.dirname(os.path.abspath(__file__))
save_path = os.path.join(here,'./Analysis results/2025-02-02.ttl')
files = [save_path]

for file in files:
    # Load the existing TTL file
    g = Graph()
    g.parse(file, format='turtle')
    
    analysis_date = file.name.split('.')[0]
    date_obj = datetime.strptime(analysis_date, "%Y-%m-%d")
    # Format as ISO 8601 with time set to 00:00:00Z
    iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Define namespaces
    DQV = Namespace("http://www.w3.org/ns/dqv#")
    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    SDMX = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
    SDMX_CODE = Namespace("http://purl.org/linked-data/sdmx/2009/code#")
    PROV = Namespace("http://www.w3.org/ns/prov#")

    # Bind namespaces   
    g.bind("dqv", DQV)
    g.bind("dcat", DCAT)
    g.bind("sdmx", SDMX)
    g.bind("sdmx-code", SDMX_CODE)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("prov", PROV)

    # Example values (you can modify these based on your actual data)
    kgheartbeat_uri = URIRef("http://example.org/assessment-tool/KGHeartBeat")
    g.add((kgheartbeat_uri, RDF.type, PROV.SoftwareAgent))
    g.add((kgheartbeat_uri, RDFS.label, Literal('A KG quality assessment tool',lang="en")))

    # Iterate over the existing triples in the graph
    for subj, pred, obj in g:
        # Check if the subject is a dqv:QualityMeasurement (to identify observations)
        if isinstance(subj, URIRef) and 'observation' in str(subj):
            # Extract the existing observation URI and modify it by appending the analysis date
            base_uri = str(subj)
            if analysis_date not in base_uri:
                new_observation_uri = URIRef(base_uri + "_" + analysis_date)
            
                # Remove old triples for the modified observation URI (if you need to delete the old ones)
                g.remove((subj, None, None))  # Remove all triples with the old observation URI
                
                # Add new triples with the updated URI
                g.add((new_observation_uri, pred, obj))
                
                # Add new statements for generatedAtTime and wasAttributedTo
                g.add((new_observation_uri, URIRef("http://www.w3.org/ns/prov#generatedAtTime"), Literal(iso_date, datatype=XSD.dateTime)))
                g.add((new_observation_uri, URIRef("http://www.w3.org/ns/prov#wasAttributedTo"), kgheartbeat_uri))

    # Save the updated graph to a new TTL file
    g.serialize(destination=file, format='turtle')

    print(f"RDF graph updated and saved to {file}")
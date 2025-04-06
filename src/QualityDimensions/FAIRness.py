import json
class FAIRness:
    def __init__(self):
        self.f1M = 0
        self.f1D = 0
        self.f2aM = 0
        self.f2bM = 0
        self.f3M = 0
        self.f4M = 0
        self.f_score = 0
        self.a1D = 0
        self.a1M = 0
        self.a1_2 = 0
        self.a2M = 0
        self.a_score = 0
        self.r1_1 = 0
        self.r1_2 = 0
        self.r1_3D = 0
        self.r1_3M = 0
        self.r_score = 0
        self.i1D = 0
        self.i1M = 0
        self.i2 = 0
        self.i3D = 0
        self.i_score = 0
        self.fair_score = 0
    
    def printFAIRness(self):
        print(f"F1-M Unique and persistent ID: {self.f1M}")
        print(f"F1-D URIs dereferenceability: {self.f1D}")
        print(f"F2a-M - Metadata availability via standard primary sources: {self.f2aM}")
        print(f"F2b-M Metadata availability for all the attributes covered in the FAIR score computation: {self.f2bM}")
        print(f"F3-M Data referrable via a DOI: {self.f3M}")
        print(f"F4-M Metadata registered in a searchable engine: {self.f4M}")
        print(f"F score: {self.f_score}")
        print(f"A1-D Working access point(s): {self.a1D}")
        print(f"A1-M Metadata availability via working primary sources: {self.a1M}")
        print(f"A1.2 Authentication & HTTPS support: {self.a1_2}")
        print(f"A2-M Registered in search engines: {self.a2M}")
        print(f"A score: {self.a_score}")
        print(f"R1.1 Machine- or human-readable license retrievable via any primary source: {self.r1_1}")
        print(f"R1.2 Publisher information, such as authors, contributors, publishers, and sources: {self.r1_2}")
        print(f"R1.3-D Data organized in a standardized way: {self.r1_2}")
        print(f"R1.3-M Metadata are described with VoID/DCAT predicates: {self.r1_3M}")
        print(f"R score: {self.r_score}")
        print(f"I1-D Standard & open representation format: {self.i1D}")
        print(f"I1-M Metadata are described with VoID/DCAT predicates: {self.i1M}")
        print(f"I2 Use of FAIR vocabularies: {self.i2}")
        print(f"I3-D Degree of connection: {self.i3D}")
        print(f"I score: {self.i_score}")
        print(f"FAIR score: {self.fair_score}")

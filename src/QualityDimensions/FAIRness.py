class FAIRness:
    def __init__(self):
        self.f1M = 0
        self.f1D = 0
        self.f2aM = 0
        self.f2bM = 0
        self.f3M = 0
        self.f4M = 0
        self.f_score = 0
    
    def printFAIRness(self):
        print(f"F1-M Unique and persistent ID: {self.f1M}")
        print(f"F1-D URIs dereferenceability: {self.f1D}")
        print(f"F2a-M - Metadata availability via standard primary sources: {self.f2aM}")
        print(f"F2b-M Metadata availability for all the attributes covered in the FAIR score computation: {self.f2bM}")
        print(f"F3-M Data referrable via a DOI: {self.f3M}")
        print(f"F4-M Metadata registered in a searchable engine: {self.f4M}")
        print(f"F score: {self.f_score}")
        
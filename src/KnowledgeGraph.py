from QualityDimensions.Accuracy import Accuracy
from QualityDimensions.AmountOfData import AmountOfData
from QualityDimensions.Availability import Availability
from QualityDimensions.Believability import Believability
from QualityDimensions.Completeness import Completeness
from QualityDimensions.Conciseness import Conciseness
from QualityDimensions.Consistency import Consistency
from QualityDimensions.Currency import Currency
from QualityDimensions.Extra import Extra
from QualityDimensions.Interlinking import Interlinking
from QualityDimensions.Interpretability import Interpretability
from QualityDimensions.Licensing import Licensing
from QualityDimensions.Performance import Performance
from QualityDimensions.RepresentationalConciseness import RepresentationalConciseness
from QualityDimensions.RepresentationalConsistency import RepresentationalConsistency
from QualityDimensions.Reputation import Reputation
from QualityDimensions.Security import Security
from QualityDimensions.Understendability import Understendability
from QualityDimensions.Verifiability import Verifiability
from QualityDimensions.Versatility import Versatility
from QualityDimensions.Volatility import Volatility

class KnowledgeGraph:
    def __init__(self,availability,currency,versatility,security,rConciseness,licensing,performance,amountOfData,volatility,interlinking,consistency,reputation,believability,verifiability,completeness,rConsistency,understendability,interpretability,conciseness,accuracy,extra):
        self.availability = availability
        self.currency = currency
        self.versatility = versatility
        self.security = security
        self.rConciseness = rConciseness
        self.licensing = licensing
        self.performance = performance
        self.amountOfData = amountOfData
        self.volatility = volatility
        self.interlinking = interlinking
        self.consistency = consistency
        self.reputation = reputation 
        self.believability = believability
        self.verifiability = verifiability
        self.completeness = completeness
        self.rConsistency = rConsistency
        self.understendability = understendability
        self.interpretability = interpretability
        self.conciseness = conciseness
        self.accuracy = accuracy
        self.extra = extra
        self.fairness = False

    def getQualityKG(self):
        return f"Quality of KG {self.believability.title}\n {Availability.getAvailability(self.availability)} {Currency.getCurrency(self.currency)} {Versatility.getVersatility(self.versatility)} {Security.getSecurity(self.security)} {RepresentationalConciseness.getRepresentationalConciseness(self.rConciseness)} {Licensing.getLicensing(self.licensing)} {Performance.getPerformance(self.performance)} {AmountOfData.getAmountOfData(self.amountOfData)} {Volatility.getVolatility(self.volatility)} {Interlinking.getInterlinking(self.interlinking)} {Consistency.getConsistency(self.consistency)} {Reputation.getReputation(self.reputation)} {Believability.getBelievability(self.believability)} {Verifiability.getVerifiability(self.verifiability)} {Completeness.getCompleteness(self.completeness)} {RepresentationalConsistency.getRepresentationalConsistency(self.rConsistency)} {Understendability.getUnderstendability(self.understendability)} {Interpretability.getInterpretability(self.interpretability)} {Conciseness.getConciseness(self.conciseness)} {Accuracy.getAccuracy(self.accuracy)} {Extra.getExtra(self.extra)}"
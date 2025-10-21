from datetime import date
from pdb import lasti2lineno
import utils
from string import whitespace
import time
import query
import utils

AVAILABILITY_METRICS = 4
LICENSING_METRICS = 2
INTERLINKING_METRICS = 5
SECURITY_METRICS = 2
PERFORMANCE_METRICS = 2
ACCURACY_METRICS = 5
CONSISTENCY_METRICS = 5
CONCISENESS_METRICS = 2
VERIFIABILITY_METRICS = 6
REPUTATION_METRICS = 1
BELIEVABILITY_METRICS = 1
CURRENCY_METRICS = 2
VOLATILITY_METRICS = 1
COMPLETENESS_METRICS = 1
AMOUNT_METRICS = 3
REP_CONS_METRICS = 2
REP_CONC_METRICS = 2
UNDERSTANDABILITY_METRICS = 4
INTERPRETABILITY_METRICS = 2
VERSATILITY_METRICS = 3
DIMENSION_NUMER = 20

class Score:
    def __init__(self,kg,dimensionNumber):
        self.kg = kg
        self.dimensionNumber = dimensionNumber
        self.availabilityScoreValue = 0
        self.licensingScoreValue = 0
        self.interlinkingScoreValue = 0
        self.performanceScoreValue = 0
        self.accuracyScoreValue = 0
        self.consistencyScoreValue = 0
        self.concisenessScoreValue = 0
        self.verifiabilityScoreValue = 0
        self.reputationScoreValue = 0
        self.believabilityScoreValue = 0
        self.currencyScoreValue = 0
        self.volatilityScoreValue = 0
        self.completenessScoreValue = 0
        self.amountScoreValue = 0
        self.repConsScoreValue = 0
        self.repConcScoreValue = 0
        self.understScoreValue = 0
        self.interpretabilityScoreValue = 0
        self.versatilityScoreValue = 0
        self.securityScoreValue = 0
        self.totalScore = 0
        self.normalizedScore = 0
        self.labelValue = 0
        self.misplacedValue = 0
        self.undefValue = 0
        self.uriValue = 0
        self.rdfValue = 0
        self.blankValue = 0
        self.vocabsValue = 0
        self.tpValue = 0
        self.latencyValue = 0

    def availabilityScore(self,weight):
        if self.kg.availability.sparqlEndpoint == 'Available':
            url = 1
        else:
            url = 0
        if self.kg.availability.RDFDumpM == True or self.kg.availability.RDFDumpQ == True:
            dump = 1
        else:
            dump = 0
        if self.kg.availability.inactiveLinks == True:
            inactive = 0
        else:
            inactive = 1
        try:
            defValue = float(self.kg.availability.uriDef)
        except:
            defValue = 0

        return ((url + dump + inactive + defValue) * weight) / AVAILABILITY_METRICS
    
    def licensingScore(self,weight):
        if isinstance(self.kg.licensing.licenseQuery,list):
            if len(self.kg.licensing.licenseQuery) > 0:
                mr = 1
            elif isinstance(self.kg.licensing.licenseMetadata,str):
                mr = 1
            else:
                mr = 0
        elif isinstance(self.kg.licensing.licenseMetadata,str):
            mr = 1
        else:
            mr = 0
        
        if isinstance(self.kg.licensing.licenseHR,bool):
            hr = self.kg.licensing.licenseHR
            if hr == True:
                hrV = 1
            else:
                hrV = 0
        else:
            hrV = 0

        return ((mr+hrV) * weight ) / LICENSING_METRICS
    
    def interlinkingScore(self,weight):
        try:
            sameAs = int(self.kg.interlinking.sameAs)
            triples = int(self.kg.amountOfData.numTriplesQ)
            if triples > 0 and triples > sameAs:
                sameAsV = sameAs/triples
            else:
                sameAsV = 0
        except (ValueError,TypeError):
            sameAsV = 0

        try:
            skosMapping = int(self.kg.interlinking.skosMapping)
            triples = int(self.kg.amountOfData.numTriplesQ)
            if triples > 0 and triples >= skosMapping:
                skosMappingV = skosMapping/triples
            else:
                skosMappingV = 0
        except (ValueError,TypeError):
            skosMappingV = 0
        
        try:
            clustering = float(self.kg.interlinking.clustering)
        except (ValueError,TypeError):
            clustering = 0
        
        try:
            centratility = float(self.kg.interlinking.centrality)
        except (ValueError,TypeError):
            centratility = 0
        
        try:
            if(int(self.kg.amountOfData.numTriplesQ) > int(self.kg.completeness.interlinkingC)):
                exLinks = float(self.kg.completeness.interlinkingC)
            else:
                exLinks = 0
        except (ValueError,TypeError):
            exLinks = 0
        
        return ((sameAsV + clustering + centratility + exLinks + skosMappingV) * weight) / INTERLINKING_METRICS

    def securityScore(self,weigth):
        https = self.kg.security.useHTTPS
        if isinstance(https,bool):
            if https == True:
                secure = 1
            else:
                secure = 0
        else:
            secure = 0
        
        auth = self.kg.security.requiresAuth
        if isinstance(auth,bool):
            if auth == True:
                authV = 0
            else:
                authV = 1
        else:
            authV = 0
        
        return ((secure + authV) * weigth) / SECURITY_METRICS


    def performanceScore(self,weight):
        count = 0
        start_time = time.time()
        if(self.kg.availability.sparqlEndpoint == 'Available'):
            while (time.time() - start_time) < 1:
                try:
                    query.TPQuery(self.kg.extra.endpointUrl,count)
                    count = count +1
                except:
                    tp =  0.0
            if count >= 5:
                tp = 1.0
            else:
                tp = count / 200
            
            latency = []
            try:
                for i in range(10):
                    query.checkEndPoint(self.kg.extra.endpointUrl)  
                    start = time.time()       
                    latencyValue = (time.time() - start)
                    latency.append(latencyValue)
                if latency[0] < 1:
                    latencyV = 1.0
                else:
                    sumLatency = sum(latencyValue)
                    meanLatency = sumLatency/len(latencyValue)
                    latencyV = 1000 / meanLatency
            except:
                latencyV = 0.0
            self.tpValue = tp
            self.latencyValue = latencyV
            return ((tp + latencyV) * weight) / PERFORMANCE_METRICS
        else:
            return 0
    
    def accuracyScore(self,weight):
        try:
            voidLabel = float(self.kg.accuracy.emptyAnn)
        except ValueError:
            voidLabel = 0
        
        try:
            whitespace = float(self.kg.accuracy.wSA)
        except ValueError:
            whitespace = 0
        
        try:
            malformedDT = float(self.kg.accuracy.malformedDataType)
        except ValueError:
            malformedDT = 0
        
        try:
            FPValue = float(self.kg.accuracy.FPvalue)
        except ValueError:
            FPValue = 0

        try:
            IFPValue = float(self.kg.accuracy.IFPvalue)
        except ValueError:
            IFPValue = 0

        return ((voidLabel + whitespace + malformedDT + FPValue + IFPValue) * weight) / ACCURACY_METRICS


    def concisenessScore(self,weight):
        try:
            intC = self.kg.conciseness.intC
            intC = intC.split(' ',1)
            intC = float(intC[0])
            
        except ValueError:
            intC = 0

        try:
            exC = self.kg.conciseness.exC
            exC = exC.split(' ',1)
            exC = float(exC[0])
        except ValueError:
            exC = 0
        
        return ((intC + exC) * weight) / CONCISENESS_METRICS
    
    def consistencyScore(self,weight):
        try:
            disj = float(self.kg.consistency.disjointClasses)
            disjV = disj
        except ValueError:
            disjV = 0

        undefP = self.kg.extra.undefinedProperties
        undefC = self.kg.extra.undefinedClass
        classes = self.kg.extra.classes
        properties = self.kg.extra.properties
        if isinstance(undefC,list) and isinstance(classes,list) and isinstance(undefP,list) and isinstance(properties,list):
            if len(classes) + len(properties) > 0 and ((len(classes) + len(properties)) > (len(undefC) + len(undefP))):
                undefV = 1.0 - (((len(undefC) + len(undefP))/(len(classes) + len(properties))))
            else:
                undefV = 0
        else:
            undefV = 0.0

        mispC = self.kg.extra.triplesMC
        mispP = self.kg.extra.triplesMP
        triples = self.kg.amountOfData.numTriplesQ
        if isinstance(mispC,list) and isinstance(mispP,list) and isinstance(triples,int):
            if triples > 0 and (triples > (len(mispC) + len(mispP))):
                mispV = 1.0 - ((len(mispC) + len(mispP)) / triples)
            else:
                mispV = 0
        else:
            mispV = 0
        
        deprecated = self.kg.extra.deprecated
        if isinstance(deprecated,list) and isinstance(classes,list) and isinstance(properties,list):
            if len(classes) + len(properties) > 0:
                depValue = 1.0 - (len(deprecated)/(len(classes) + len(properties)))
            else:
                depValue = 0
        else:
            depValue = 0
        
        ontologyH = self.kg.consistency.oHijacking
        if isinstance(ontologyH,bool):
            if ontologyH == True:
                ohValue = 0
            else:
                ohValue = 1
        else:
            ohValue = 0
        
        self.misplacedValue = mispV
        self.undefValue = undefV
        return ((disjV + undefV + mispV + depValue +  ohValue) * weight) / CONSISTENCY_METRICS
        
    def verifiabilityScore(self,weight):
        vocabs = self.kg.verifiability.vocabularies
        if isinstance(vocabs,list):
            if len(vocabs) > 0:
                vocabsV = 1
            else:
                vocabsV = 0
        else:
            vocabsV = 0
        
        authorsQ = self.kg.verifiability.authorQ
        authorsM = self.kg.verifiability.authorM
        if isinstance(authorsM,str):
            if authorsM != '' and authorsM != ' ':
                authV = 1
            else:
                authV = 0
        else:
            if isinstance(authorsQ,list):
                if len(authorsQ) > 0:
                    authV = 1
                else:
                    authV = 0
            else:
                authV = 0
        
        publishers = self.kg.verifiability.publisher
        if isinstance(publishers,list):
            if len(publishers) > 0:
                pubV = 1
            else:
                pubV = 0
        else:
            pubV = 0
        
        contribs = self.kg.verifiability.contributor
        if isinstance(contribs,list):
            if len(contribs) > 0:
                contribsV = 1
            else:
                contribsV = 0
        else:
            contribsV = 0
        
        sources = self.kg.verifiability.sources
        srcV = 0
        if sources.web != 'absent':
            srcV = srcV + 0.33
        if sources.name != 'absent':
            srcV = srcV + 0.33
        if sources.email != 'absent':
            srcV = srcV + 0.33
        
        sign = self.kg.verifiability.sign
        if isinstance(sign,bool):
            if sign == True:
                signV = 1
            else:
                signV = 0
        else:
            signV = 0
        
        return ((vocabsV + authV + pubV + contribsV + srcV + signV) * weight) / VERIFIABILITY_METRICS
    
    def reputationScore(self,weight):
        try:
            pr = self.kg.reputation.pageRank.replace(',','.')
            pr = float(pr)
            prV = pr/10.00
        except:
            prV = 0
        
        return (prV * weight) / REPUTATION_METRICS
    
    def believabilityScore(self,weight):
        trustV = self.kg.believability.trustValue.replace(',','.')
        trustV = float(trustV)

        return (trustV * weight) / BELIEVABILITY_METRICS
    

    def currencyScore(self,weight):
        creation = self.kg.currency.creationDate
        if isinstance(creation,date) or (isinstance(creation,str) and creation != '-') or isinstance(creation,int):
                cV = 1
        else:
            cV = 0
        modification = self.kg.currency.modificationDate
        if isinstance(modification,date) or (isinstance(modification,str)and modification != '-'):
                mV = 1
        else:
            mV = 0
        
        return ((cV + mV) * weight) / CURRENCY_METRICS

    def volatilityScore(self,weight):
        frequency = self.kg.volatility.frequency
        if isinstance(frequency,list):
            if len(frequency) > 0:
                freqV = 1
            else:
                freqV = 0
        elif isinstance(frequency,str) and frequency in ['http:','https:']:
            freqV = 1
        else:
            freqV = 0
        
        return (freqV * weight) / VOLATILITY_METRICS
    
    def completenessScore(self,weight):
        try:
            if(int(self.kg.amountOfData.numTriplesQ) > float(self.kg.completeness.interlinkingC)):
                interC = float(self.kg.completeness.interlinkingC)
            else:
                interC = 0
        except:
            interC = 0
        
        return (interC * weight) / COMPLETENESS_METRICS
    
    def amountScore(self,weigth):
        try:
            numT = int(self.kg.amountOfData.numTriplesQ)
            triplesV = 1
        except (ValueError,TypeError):
            triplesV = 0
        try:
            numT = int(self.kg.amountOfData.numTriplesM)
            triplesV = 1
        except (ValueError,TypeError):
            triplesV = 0
        try:
            numERe = int(self.kg.amountOfData.entitiesRe)
            entitiesV = 1
        except (ValueError,TypeError):
            entitiesV = 0
        if entitiesV == 0:
            try:
                numE = int(self.kg.amountOfData.numEntities)
                entitiesV = 1
            except (ValueError,TypeError):
                entitiesV = 0
        try:
            numProp = int(self.kg.amountOfData.numProperty)
            numPropV = 1
        except (ValueError,TypeError):
            numPropV = 0
        
        return ((triplesV + entitiesV + numPropV ) * weigth) / AMOUNT_METRICS

    def repConcScore(self,weight):
        allUri = self.kg.extra.uriList
        sparqlUrl = self.kg.extra.endpointUrl
        if(self.kg.availability.sparqlEndpoint == 'Available'):
            urlApproved = []
            for uri in allUri:
                if len(uri) < 80 and '?' not in uri:
                    urlApproved.append(uri)
            try:
                dlc = query.getDlc(sparqlUrl)
                if isinstance(dlc,int):
                    if dlc > 0 and dlc > len(urlApproved):
                        uriV = len(urlApproved) / dlc
                    else:
                        uriV = 0
                else:
                    uriV = 0
            except:
                uriV = 0

            try:
                rcc = query.countStruct(sparqlUrl)
                if isinstance(rcc,int):
                    triples = int(self.kg.amountOfData.numTriplesQ)
                    if(triples > rcc):
                        rdfV = 1.0 - (rcc/triples)
                    else:
                        rdfV = 0
                else:
                    rdfV = 0
            except:
                rdfV = 0
        else:
            rdfV = 0
            uriV = 0
        
        self.uriValue = uriV
        self.rdfValue = rdfV
        return ((uriV + rdfV) * weight) / REP_CONC_METRICS
    
    def repConsScore(self,weight):
        allTerms = self.kg.extra.allTerms
        newTerms = self.kg.rConsistency.useNewTerms
        if isinstance(allTerms,list) and isinstance(newTerms,list):
            if len(allTerms) > 0:
                if(len(allTerms) > len(newTerms)):
                    repConsV = 1.0 - (len(newTerms)/len(allTerms))
                else:
                    repConsV = 0
            else:
                repConsV = 0
        else:
            repConsV = 0
    
        newVocabs = self.kg.rConsistency.newVocab
        if isinstance(newVocabs,list):
            if len(newVocabs) > 0:
                newVocabsV = 0
            else:
                newVocabsV = 1
        else:
            newVocabsV = 0

        return ((repConsV + newVocabsV) * weight) / REP_CONS_METRICS
    
    def understScore(self,weight):
        sparqlUrl = self.kg.extra.endpointUrl
        if self.kg.availability.sparqlEndpoint == 'Available':
            try:
                allSubject = utils.run_with_timeout(query.getNumS, args=(sparqlUrl,), timeout=300)
                numLabel = self.kg.understendability.numLabel
                if allSubject > 0 and isinstance(numLabel,int):
                    if allSubject >= numLabel:
                        labelV = numLabel/allSubject
                    else:
                        labelV = 0
                else:
                    labelV = 0
            except:
                labelV = 0
        else:
            labelV = 0

        regex = self.kg.understendability.regexUri
        if isinstance(regex,list):
            if len(regex) > 0:
                regexV = 1
            else:
                regexV = 0
        else:
            regexV = 0
        
        example = self.kg.understendability.example
        if isinstance(example,bool):
            if example == True:
                exampleV = 1
            else:
                exampleV = 0
        else:
            exampleV = 0
        
        vocabs = self.kg.understendability.vocabularies
        allTerms = self.kg.extra.allTerms
        if isinstance(vocabs,list) and isinstance(allTerms,list):
            namespaces = utils.getURINamespace(allTerms)
            if len(namespaces) > 0 and len(namespaces) >= len(vocabs):
                vocabsV = len(vocabs) / len(namespaces)
            else:
                vocabsV = 0
        else:
            vocabsV = 0
        
        self.labelValue = labelV
        self.vocabsValue = vocabsV
        return ((labelV + regexV + exampleV + vocabsV)  * weight) / UNDERSTANDABILITY_METRICS
    
    def interpretabilityScore(self,weight):
        sparqlUrl = self.kg.extra.endpointUrl
        if self.kg.availability.sparqlEndpoint == 'Available':
            try:
                bnNumber = query.getNumDlcBN(sparqlUrl)
                numDlc = query.getDlc(sparqlUrl)
                if isinstance(bnNumber,int) and isinstance(numDlc,int):
                    if numDlc > 0 and numDlc > bnNumber:
                        bnValue = 1 - (bnNumber/numDlc)
                    else:
                        bnValue = 0
                else:
                    bnValue = 0
            except:
                bnValue = 0
            try:
                rcc = query.countStruct(sparqlUrl)
                if isinstance(rcc,int):
                    rdfV = 1.0 - (rcc/int(self.kg.amountOfData.numTriplesQ))
                else:
                    rdfV = 0
            except:
                rdfV = 0
        else:
            bnValue = 0
            rdfV = 0
        self.blankValue = bnValue
        return ((bnValue + rdfV) * weight) /INTERPRETABILITY_METRICS
    
    def versatilityScore(self,weight):
        serializationF = self.kg.versatility.serializationFormats
        if isinstance(serializationF,list):
            if len(serializationF) > 0:
                seriValue = 1
            else:
                seriValue = 0
        else:
            seriValue = 0
        languages = self.kg.versatility.languagesQ
        if isinstance(languages,list):
            if len(languages) > 0:
                langsV = 1
            else:
                langsV = 0
        else:
            langsV = 0
        try:
            if self.kg.availability.sparqlEndpoint == 'Available' and (self.kg.availability.RDFDumpM == True or self.kg.availability.RDFDumpQ == True):
                accessibilityV = 1
            else : 
                accessibilityV = 0
        except:
            accessibilityV = 0
        
        return ((seriValue + langsV + accessibilityV) * weight) / VERSATILITY_METRICS
    
    def getWeightedDimensionScore(self,weight):
        self.availabilityScoreValue = self.availabilityScore(weight)
        self.licensingScoreValue = self.licensingScore(weight)
        self.interlinkingScoreValue = self.interlinkingScore(weight)
        self.securityScoreValue = self.securityScore(weight)
        self.performanceScoreValue = self.performanceScore(weight)
        self.accuracyScoreValue = self.accuracyScore(weight)
        self.consistencyScoreValue = self.consistencyScore(weight)
        self.concisenessScoreValue = self.concisenessScore(weight)
        self.reputationScoreValue = self.reputationScore(weight)
        self.believabilityScoreValue = self.believabilityScore(weight)
        self.verifiabilityScoreValue = self.verifiabilityScore(weight)
        self.currencyScoreValue = self.currencyScore(weight)
        self.volatilityScoreValue = self.volatilityScore(weight)
        self.completenessScoreValue = self.completenessScore(weight)
        self.amountScoreValue = self.amountScore(weight)
        self.repConcScoreValue = self.repConcScore(weight)
        self.repConsScoreValue = self.repConsScore(weight)
        self.understScoreValue = self.understScore(weight)
        self.interpretabilityScoreValue = self.interpretabilityScore(weight)
        self.versatilityScoreValue = self.versatilityScore(weight)
        score = (self.availabilityScoreValue + self.licensingScoreValue + self.interlinkingScoreValue + self.securityScoreValue + self.performanceScoreValue + self.accuracyScoreValue + self.consistencyScoreValue + self.concisenessScoreValue + self.reputationScoreValue + self.believabilityScoreValue + self.verifiabilityScoreValue + self.currencyScoreValue + self.volatilityScoreValue + self.completenessScoreValue + self.amountScoreValue + self.repConcScoreValue + self.repConsScoreValue + self.understScoreValue +  self.interpretabilityScoreValue + self.versatilityScoreValue) / DIMENSION_NUMER
        if score > 0:
            normalized_score = utils.normalize_score(score)
            self.totalScore = score
            self.normalizedScore = normalized_score
            return score,normalized_score
        else:
            self.totalScore = 0
            self.normalizedScore = 0
            return 0,0

    def to_dict(self):
        score_dict = {
            'dimensionNumber' : self.dimensionNumber,
            'totalScore' : self.totalScore,
            'normalizedScore' : self.normalizedScore,
            'availabilityScoreValue' : self.availabilityScoreValue,
            'licensingScoreValue' : self.licensingScoreValue ,
            'interlinkingScoreValue' : self.interlinkingScoreValue,
            'performanceScoreValue' : self.performanceScoreValue,
            'accuracyScoreValue' : self.accuracyScoreValue,
            'consistencyScoreValue' : self.consistencyScoreValue,
            'concisenessScoreValue' : self.concisenessScoreValue,
            'verifiabilityScoreValue' : self.verifiabilityScoreValue, 
            'reputationScoreValue' : self.reputationScoreValue, 
            'believabilityScoreValue' : self.believabilityScoreValue, 
            'currencyScoreValue' : self.currencyScoreValue,
            'volatilityScoreValue' : self.volatilityScoreValue,
            'completenessScoreValue': self.completenessScoreValue,
            'amountScoreValue' : self.amountScoreValue ,
            'repConsScoreValue' : self.repConsScoreValue,
            'repConcScoreValue' : self.repConcScoreValue,
            'understScoreValue' : self.understScoreValue,
            'interpretabilityScoreValue' : self.interpretabilityScoreValue,
            'versatilityScoreValue' : self.versatilityScoreValue,
            'securityScoreValue' : self.securityScoreValue 
        }
        return score_dict



        
            





    

        
    
        


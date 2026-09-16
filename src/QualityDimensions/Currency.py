import datetime

import query
from QualityDimensions.base import MISSING_VALUE


class Currency:
    def __init__(self,creationDate, modificationDate,percentageUpData,timePassed,historicalUp):
        self.creationDate = creationDate
        self.modificationDate = modificationDate
        self.percentageUpData = percentageUpData
        self.timePassed = timePassed
        self.historicalUp = historicalUp

    
    def to_dict(self):
        return {
            "creationDate" : str(self.creationDate),
            "modificationDate" : str(self.modificationDate),
            "percentageUpData" : str(self.percentageUpData),
            "timePassed" : str(self.timePassed),
            "historicalUp" : str(self.historicalUp),
        }

    def getCurrency(self):
        return f"-Currency\n   Cretion date:{self.creationDate}\n   Modification date:{self.modificationDate}\n   Percentage of data updated:{self.percentageUpData}\n   Time elapsed from data creation to the last modification:{self.timePassed} days\n   Historical updates:{self.historicalUp}\n"


def endpoint_dates(context):
    creation_date = _creation_date(context)
    modification_date = _modification_date(context)
    historical_updates = _historical_updates(context)
    updated_triples = _updated_triples(context, modification_date)
    return creation_date, modification_date, historical_updates, updated_triples


def build(context, creation_date, modification_date, updated_triples, triples_query, triples_metadata, historical_updates):
    percentage_up = updated_percentage(context, updated_triples, triples_query, triples_metadata)
    if isinstance(creation_date, str) and isinstance(modification_date, str):
        try:
            creation = datetime.datetime.strptime(creation_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            age_of_data = (today - creation).days
            modification = datetime.datetime.strptime(modification_date, "%Y-%m-%d").date()
            delta = (today - modification).days
            return Currency(age_of_data, modification, percentage_up, delta, historical_updates)
        except Exception:
            context.warning("Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | Insufficient data to compute this metric")
            return Currency(creation_date, modification_date, percentage_up, MISSING_VALUE, historical_updates)

    context.warning("Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | Insufficient data to compute this metric")
    return Currency(creation_date, modification_date, percentage_up, MISSING_VALUE, historical_updates)


def build_void(context, creation_date, modification_date):
    if isinstance(creation_date, str) and isinstance(modification_date, str):
        try:
            creation = datetime.datetime.strptime(creation_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            age_of_data = (today - creation).days
            modification = datetime.datetime.strptime(modification_date, "%Y-%m-%d").date()
            delta = (today - modification).days
            return Currency(age_of_data, modification, 'insufficient data', delta, 'insufficient data')
        except Exception as error:
            context.warning(f"Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | {str(error)}")
            return Currency(creation_date, modification_date, MISSING_VALUE, MISSING_VALUE, MISSING_VALUE)

    context.warning("Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | No triples with dcterms:modified predicate")
    return Currency(creation_date, modification_date, MISSING_VALUE, MISSING_VALUE, MISSING_VALUE)


def updated_percentage(context, updated_triples, triples_query, triples_metadata):
    if isinstance(triples_query, int) and isinstance(updated_triples, int) and triples_query > 0:
        return f"{(updated_triples / triples_query) * 100}%"
    if isinstance(triples_metadata, int) and isinstance(updated_triples, int) and triples_metadata > 0:
        return f"{(updated_triples / triples_metadata) * 100}%"
    context.warning("Currency | Update history | Insufficient data to compute this metric")
    return MISSING_VALUE


def _creation_date(context):
    try:
        return context.timed('Creation date check', 'Currency', lambda: query.getCreationDateMin(context.access_url) or query.getCreationDate(context.access_url))
    except Exception:
        try:
            return query.getCreationDate(context.access_url)
        except Exception as error:
            context.warning(f'Currency | Age of data | {str(error)}')
            return MISSING_VALUE


def _modification_date(context):
    try:
        return context.timed('Modification date check', 'Currency', lambda: query.getModificationDateMax(context.access_url) or query.getModificationDate(context.access_url))
    except Exception:
        try:
            return query.getModificationDate(context.access_url)
        except Exception as error:
            context.warning(f'Currency | Specification of the modification date of statements | {error}')
            return MISSING_VALUE


def _historical_updates(context):
    try:
        updates = []
        date_updates = query.getDateUpdates(context.access_url)
        if isinstance(date_updates, list):
            unique_dates = list(set(date_updates))
            unique_dates.sort(key=lambda date: datetime.datetime.strptime(date, "%Y-%m-%d"))
            for item in unique_dates:
                date = str(item)
                num = query.getNumUpdatedData(context.access_url, date)
                updates.append(f"{date}|{num}".strip())
        return updates
    except Exception as error:
        context.warning(f'Currency | Update history | {str(error)}')
        return MISSING_VALUE


def _updated_triples(context, modification_date):
    try:
        return query.getNumUpdatedData(context.access_url, modification_date)
    except Exception as error:
        context.warning(f'Currency | Number of triples updated | {str(error)}')
        return MISSING_VALUE

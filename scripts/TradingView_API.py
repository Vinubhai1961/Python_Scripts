from nasdaq import NASDAQDataIngestor

ingestor = NASDAQDataIngestor()
profile = ingestor.fetch_company_profile("AAPL")
print(profile)  # includes industry/sector
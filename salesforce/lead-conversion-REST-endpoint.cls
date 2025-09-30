@RestResource(urlMapping='/convertLeadToContact') // this prefixed with your salesforce instance url will be the endpoint

global with sharing class LeadConversionService {

@HttpPost
global static String convertLeadAndAttachAccount() {
    try {
        // Access request body from RestContext
        String requestBody = RestContext.request.requestBody.toString();
        Map<String, String> params = (Map<String, String>) JSON.deserialize(requestBody, Map<String, String>.class);

        String leadId = params.get('leadId');
        String accountId = params.get('accountId');

        if (String.isBlank(leadId) || String.isBlank(accountId)) {
            RestContext.response.statusCode = 400;
            return 'Missing leadId or accountId.';
        }
        // Queries for the lead to check if it already exists as contact
        Lead leadToConvert = [SELECT Id, IsConverted FROM Lead WHERE Id = :leadId LIMIT 1];
        if (leadToConvert.IsConverted) {
            RestContext.response.statusCode = 400;
            return 'Lead is already converted.';
        }

        // Conversion setup
        Database.LeadConvert lc = new Database.LeadConvert();
        lc.setLeadId(leadId);
        lc.setDoNotCreateOpportunity(true); // Set to flase if you do want an opportunity created
        lc.setConvertedStatus('Converted'); // Ensure this matches your org
        lc.setAccountId(accountId);

        Database.LeadConvertResult lcr = Database.convertLead(lc);

        if (lcr.isSuccess()) {
            return 'Lead converted successfully. Contact ID: ' + lcr.getContactId();
        } else {
            RestContext.response.statusCode = 500;
            return 'Lead conversion failed: ' + lcr.getErrors()[0].getMessage();
        }

    } catch (Exception e) {
        RestContext.response.statusCode = 500;
        return 'Error: ' + e.getMessage();
    }
}
}

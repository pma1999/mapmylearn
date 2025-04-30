import React from 'react';
import { Container, Typography, Box, Link, List, ListItem, ListItemText } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink } from 'react-router';

const PrivacyPolicyPage = () => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Helmet>
        <title>Privacy Policy | MapMyLearn</title>
        <meta name="description" content="Read the Privacy Policy for MapMyLearn." />
      </Helmet>
      
      <Typography variant="h4" component="h1" gutterBottom>
        Privacy Policy for MapMyLearn
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        Last Updated: April 30, 2025
      </Typography>

      <Typography paragraph>
        Welcome to MapMyLearn. Your privacy is important to us. This Privacy Policy explains how Pablo Miguel Argudo ("we", "our") collects, uses, discloses, and protects your personal information when you use our application and services (hereinafter, "the Service").
      </Typography>
       <Typography paragraph>
        By using the Service, you agree to the practices described in this Privacy Policy. If you do not agree, please do not use the Service.
      </Typography>
      
      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        1. Data Controller
      </Typography>
       <List dense>
          <ListItem sx={{ pl: 2 }}><ListItemText primary="Identity: Pablo Miguel Argudo" /></ListItem>
          <ListItem sx={{ pl: 2 }}><ListItemText primary="Contact: pablomiguelargudo@gmail.com" /></ListItem>
          <ListItem sx={{ pl: 2 }}><ListItemText primary="Location: Valencia, Spain" /></ListItem>
       </List>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        2. Information We Collect
      </Typography>
      <Typography paragraph>
        We collect different types of information to provide and improve our Service:
      </Typography>
       <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Information Provided by the User:
      </Typography>
      <List dense>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Registration Data: When you create an account, we collect your full name, email address, and password (we store a secure hash of your password, not the password itself)." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Contact Data: If you contact us via email or other means, we may keep a record of that correspondence." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Learning Topics: We collect the topics or subjects you enter to generate learning paths." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="(Optional) External API Keys: If you choose to use your own API keys (e.g., Google AI, Brave Search/Perplexity), we may store them temporarily and securely (encrypted and with an access token) to facilitate their use within the Service, as described in our T&C. We only store these keys if you select the 'remember' option." /></ListItem>
      </List>
        <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Information Collected Automatically:
      </Typography>
        <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Usage Data: We collect information about how you interact with the Service, such as generated paths, paths saved to history, features used (e.g., audio generation, PDF export), access dates and times, and interface interactions." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Path History: If registered, we store the learning paths you generate and choose to save in your history, including their content and metadata like creation date." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Credit Information: We record your credit balance and associated transactions (purchase and consumption). If you purchase credits, our payment provider (Stripe) collects your payment information directly; we only receive transaction confirmation and limited data (like card type or last digits) for management purposes." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Technical Data: We collect technical information about your device and connection, such as IP address, browser type, operating system, device identifiers (if applicable), and Service performance data." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Analytics Data: We use analytics services (like Vercel Analytics) to collect aggregated and anonymous or pseudonymous information about Service usage to understand usage patterns and improve the platform." /></ListItem>
       </List>
        <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Cookies and Similar Technologies:
      </Typography>
         <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="We use essential cookies for the Service to function (e.g., user session management, security). These are necessary for the operation of the site and cannot be disabled in our systems." /></ListItem>
         </List>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        3. How We Use Your Information
      </Typography>
       <Typography paragraph>
        We use the collected information for the following purposes:
      </Typography>
       <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Provide and Maintain the Service: Operate the platform, authenticate users, generate and display learning paths, manage history, process credit purchases, etc." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Personalize Experience: Adapt content and features to your preferences." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Improve the Service: Analyze usage to identify areas for improvement, fix errors, and develop new features." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Communication: Send you service-related emails (e.g., account verification, registration confirmation, important notifications about your account or changes to services/policies, password recovery). We will not send marketing communications without your explicit consent." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Security: Protect the security and integrity of the Service, prevent fraud and abuse." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Legal Compliance: Comply with our legal and regulatory obligations." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Credit Management: Manage your credit balance and transactions." /></ListItem>
       </List>

       <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        4. Legal Basis for Processing (Users in EEA/Spain)
      </Typography>
       <Typography paragraph>
        We process your personal information based on the following legal bases under GDPR:
      </Typography>
       <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Performance of a Contract: Processing is necessary to fulfill our Terms and Conditions and provide the Service you requested (e.g., registration, path generation, history)." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Consent: For certain activities, like sending marketing communications (if applicable) or using non-essential cookies, we will request your explicit consent. You can withdraw consent at any time." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Legitimate Interests: We process certain data for our legitimate interests, such as improving the Service, ensuring security, and preventing fraud, provided these interests do not override your fundamental rights and freedoms." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Legal Obligation: We may process your data to comply with applicable legal obligations." /></ListItem>
       </List>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        5. How We Share Your Information
      </Typography>
      <Typography paragraph>
         We do not sell your personal information. We may share it with third parties only in the following circumstances:
      </Typography>
       <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Service Providers:
      </Typography>
      <Typography paragraph>
        We share information with third parties that help us operate the Service, such as:
      </Typography>
      <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Web hosting providers (e.g., Railway, Vercel)." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="AI service providers (e.g., Google AI, for content generation)." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Web search service providers (e.g., Brave Search/Perplexity, if used)." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Payment processors (e.g., Stripe, to manage credit purchases)." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Analytics providers (e.g., Vercel Analytics)." /></ListItem>
       </List>
      <Typography paragraph>
          These providers only have access to the information necessary to perform their functions and are contractually obligated to protect it.
      </Typography>
        <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Legal Compliance and Security:
      </Typography>
        <Typography paragraph>
        We may disclose your information if we believe in good faith it is necessary to:
      </Typography>
        <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Comply with a legal obligation, judicial process, or governmental request." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Enforce our Terms and Conditions and other policies." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Protect our rights, property, or safety, or those of our users or others." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Detect, prevent, or address fraud, security, or technical issues." /></ListItem>
       </List>
        <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Business Transfers:
      </Typography>
        <Typography paragraph>
        In the event of a merger, acquisition, reorganization, or sale of assets, your information may be transferred as part of the transaction. We will notify you of such events and the choices you may have regarding your information.
      </Typography>
      
       <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        6. International Data Transfers
      </Typography>
        <Typography paragraph>
         Some of the service providers we use (e.g., Google AI, Stripe, Vercel) may be located outside the European Economic Area (EEA). When we transfer your personal information outside the EEA, we ensure that adequate safeguards are in place to protect it, such as:
        </Typography>
        <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Adequacy decisions from the European Commission." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Standard Contractual Clauses (SCCs) approved by the European Commission." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Other legal mechanisms permitted by applicable law." /></ListItem>
       </List>

       <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        7. Data Retention
      </Typography>
        <Typography paragraph>
        We will retain your personal information only for as long as necessary to fulfill the purposes for which it was collected, including providing the Service, complying with legal obligations, resolving disputes, and enforcing our agreements.
        </Typography>
         <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Account Data: Retained while your account is active. If you request account deletion, we will securely delete your personal data, except for data we must retain due to legal obligations (e.g., billing data if you purchased credits) or for defense against potential claims, during the legal limitation periods." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Path History: Retained while your account is active or until you decide to delete specific entries or your entire account." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Usage and Technical Data: May be retained in aggregated or anonymized form for longer periods for analysis and service improvement purposes." /></ListItem>
       </List>

       <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        8. Your Data Protection Rights (GDPR/LOPDGDD)
      </Typography>
        <Typography paragraph>
        If you reside in the EEA or Spain, you have the following rights regarding your personal information:
        </Typography>
         <List dense>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right of Access: Request a copy of the personal information we hold about you." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right to Rectification: Request correction of inaccurate or incomplete personal information." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right to Erasure ('Right to be Forgotten'): Request the deletion of your personal information under certain conditions." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right to Restriction of Processing: Request that we restrict the processing of your personal information under certain conditions." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right to Data Portability: Receive the personal information you provided to us in a structured, commonly used, and machine-readable format, and transmit it to another data controller." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right to Object: Object to the processing of your personal information based on our legitimate interests." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right to Withdraw Consent: If processing is based on your consent, you can withdraw it at any time." /></ListItem>
           <ListItem sx={{ pl: 2 }}><ListItemText primary="Right not to be subject to Automated Decision-making: You have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning you or similarly significantly affects you." /></ListItem>
       </List>
        <Typography paragraph>
         To exercise these rights, please contact us at: pablomiguelargudo@gmail.com. We may need to verify your identity before processing your request.
        </Typography>
        <Typography paragraph>
         You also have the right to lodge a complaint with the Spanish Data Protection Agency (AEPD) if you believe that the processing of your personal data infringes applicable regulations.
        </Typography>

       <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        9. Information Security
      </Typography>
         <Typography paragraph>
         We implement reasonable technical and organizational security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. These measures include the use of encryption (e.g., HTTPS, encryption of stored API keys), access controls, and secure development practices. However, no electronic transmission or storage system is 100% secure, so we cannot guarantee absolute security.
        </Typography>

       <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        10. Children's Privacy
      </Typography>
       <Typography paragraph>
        The Service is not directed to children under 14 years of age (or the applicable minimum legal age in your jurisdiction to consent to data processing). We do not knowingly collect personal information from children under that age. If we discover that we have collected personal information from a child without required parental consent, we will take steps to delete it as soon as possible. If you are a parent or guardian and believe your child has provided us with personal information, please contact us.
        </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        11. Changes to this Privacy Policy
      </Typography>
       <Typography paragraph>
       We may update this Privacy Policy periodically. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date. We encourage you to review this Policy periodically to stay informed about how we protect your information. Continued use of the Service after the changes are posted will constitute your acceptance of those changes.
        </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        12. Contact Us
      </Typography>
        <Typography paragraph>
        If you have any questions or concerns about this Privacy Policy or our data practices, please contact us at:
        </Typography>
        <Typography paragraph sx={{ pl: 2 }}>
         Pablo Miguel Argudo<br />
         Email: pablomiguelargudo@gmail.com<br />
         Valencia, Spain
        </Typography>

    </Container>
  );
};

export default PrivacyPolicyPage; 
import React from 'react';
import { Container, Typography, Box, Link, List, ListItem, ListItemText } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink } from 'react-router';

const TermsPage = () => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Helmet>
        <title>Terms and Conditions | MapMyLearn</title>
        <meta name="description" content="Read the Terms and Conditions for using MapMyLearn." />
      </Helmet>
      
      <Typography variant="h4" component="h1" gutterBottom>
        Terms and Conditions of Use for MapMyLearn
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        Last Updated: April 30, 2025
      </Typography>

      <Typography paragraph>
        Welcome to MapMyLearn (hereinafter, "the Service" or "the Platform"), an application designed to generate personalized learning paths using artificial intelligence. These Terms and Conditions (hereinafter, "T&C") govern the access and use of the Platform by users (hereinafter, "User" or "Users").
      </Typography>
      <Typography paragraph>
        By registering or using the Service, you agree to be bound by these T&C and our <Link href="/privacy">Privacy Policy</Link>. If you do not agree with any part of these terms, you must not use the Service.
      </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        1. Service Provider Identification
      </Typography>
      <List dense>
        <ListItem>
          <ListItemText primary="Owner: Pablo Miguel Argudo" />
        </ListItem>
        <ListItem sx={{ pl: 2 }}>
          <ListItemText primary="Contact Email: pablomiguelargudo@gmail.com" />
        </ListItem>
      </List>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        2. Object and Description of the Service
      </Typography>
      <Typography paragraph>
        MapMyLearn is a platform that uses advanced language models and web search capabilities to generate structured learning paths on various topics requested by the User. The Service includes:
      </Typography>
      <List dense>
          <ListItem><ListItemText primary="Generation of learning paths with modules and submodules." /></ListItem>
          <ListItem><ListItemText primary="Personalization based on the topic and optional parameters provided by the User." /></ListItem>
          <ListItem><ListItemText primary="Storage of the history of generated paths for registered Users." /></ListItem>
          <ListItem><ListItemText primary="Generation of audio summaries for submodules (may require credits)." /></ListItem>
          <ListItem><ListItemText primary="Credit system to access specific features." /></ListItem>
          <ListItem><ListItemText primary="Possibility to export paths to PDF." /></ListItem>
          <ListItem><ListItemText primary="(If applicable) Use of external API keys provided by the user." /></ListItem>
      </List>


      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        3. Registration and User Account
      </Typography>
      <List dense>
        <ListItem><ListItemText primary="Need for Registration: To access certain functionalities, such as saving path history, generating audio, or purchasing credits, registration by creating an account is necessary." /></ListItem>
        <ListItem><ListItemText primary="Registration Information: The User agrees to provide truthful, accurate, and up-to-date information during the registration process (Full name, email address)." /></ListItem>
        <ListItem><ListItemText primary="Account Responsibility: The User is responsible for maintaining the confidentiality of their password and for all activities that occur under their account. They must immediately notify MapMyLearn of any unauthorized use of their account via pablomiguelargudo@gmail.com." /></ListItem>
        <ListItem><ListItemText primary="Minimum Age: The Service is intended for users over 14 years of age or the minimum legal age to consent to personal data processing in Spain. If you are a minor, you need the consent of your parents or legal guardians." /></ListItem>
      </List>
      
      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        4. Acceptable Use of the Service
      </Typography>
      <Typography paragraph>
        The User agrees to use the Service in accordance with the law, morality, public order, and these T&C. It is expressly prohibited to:
      </Typography>
       <List dense>
          <ListItem><ListItemText primary="Use the Service for illicit purposes or purposes harmful to the rights and interests of third parties." /></ListItem>
          <ListItem><ListItemText primary="Attempt unauthorized access to the Platform, other users' accounts, computer systems, or networks connected to the Service." /></ListItem>
          <ListItem><ListItemText primary="Introduce viruses, malicious code, or any other harmful software." /></ListItem>
          <ListItem><ListItemText primary="Use the Service in a way that could damage, overload, or impair the Platform or interfere with the normal use by other Users." /></ListItem>
          <ListItem><ListItemText primary="Use automated means (bots, scrapers) to access or interact with the Service without explicit permission." /></ListItem>
          <ListItem><ListItemText primary="Resell or commercially exploit the Service without prior authorization." /></ListItem>
      </List>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        5. Intellectual and Industrial Property
      </Typography>
       <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Of the Platform:
      </Typography>
      <Typography paragraph>
         MapMyLearn and all its contents (source code, graphic design, user interface, texts, logos, trademarks, etc.) are the exclusive property of Pablo Miguel Argudo or its licensors, and are protected by Spanish and international intellectual and industrial property laws.
      </Typography>
        <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Of the Generated Content:
      </Typography>
       <List dense>
          <ListItem><ListItemText primary="The learning paths and audios generated by the AI are the result of an automated process based on User input and public information sources and/or AI models." /></ListItem>
          <ListItem><ListItemText primary="The User receives a limited, non-exclusive, revocable, and non-transferable license to use the generated learning paths and audios solely for their personal and non-commercial learning." /></ListItem>
          <ListItem><ListItemText primary="The User acknowledges that, due to the nature of AI, the generated content may not be completely original, accurate, or complete, and may contain information from third-party sources. MapMyLearn does not claim authorship of the underlying informational content obtained from external sources or generated by the base models." /></ListItem>
      </List>
       <Typography variant="subtitle1" component="h3" gutterBottom sx={{ mt: 2 }}>
        Of User Content (History):
      </Typography>
      <Typography paragraph>
         The User retains ownership of the *idea* or *topic* they introduce to generate a path. However, by saving a path to their history, the User grants MapMyLearn a worldwide, non-exclusive, royalty-free, and transferable license to store, reproduce, and display said history *within the Platform* for the purpose of providing the Service to them.
      </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        6. External API Keys (If Applicable)
      </Typography>
      <Typography paragraph>
        If the Platform allows the User to enter their own API keys (e.g., Google AI, Perplexity/Brave), the User is solely responsible for:
      </Typography>
      <List dense>
        <ListItem><ListItemText primary="Obtaining such keys in accordance with the terms and conditions of the corresponding provider." /></ListItem>
        <ListItem><ListItemText primary="Ensuring the confidentiality and security of their keys." /></ListItem>
        <ListItem><ListItemText primary="Complying with the usage limits and costs associated with such API keys." /></ListItem>
      </List>
      <Typography paragraph>
        MapMyLearn acts merely as a technical intermediary to facilitate the use of these keys within the Platform and is not responsible for the use the User makes of them or the costs derived therefrom.
      </Typography>
      
      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        7. Privacy Policy and Data Protection
      </Typography>
       <Typography paragraph>
        The processing of Users' personal data is governed by our <Link href="/privacy">Privacy Policy</Link>, which is an integral part of these T&C. We comply with the General Data Protection Regulation (GDPR) and the Organic Law 3/2018, of December 5, on the Protection of Personal Data and guarantee of digital rights (LOPDGDD).
      </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        8. Credit System
      </Typography>
       <List dense>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Usage: Certain actions within the Platform, such as generating learning paths (1 credit) or generating audio for submodules (1 credit), consume credits. The credit cost of each action will be indicated in the interface before performing it." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Obtainment: Users receive 3 free credits upon successful registration and email verification. Additional credits can be obtained by purchasing them through the Platform." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Purchase: Credit purchase is made through an external payment provider (Stripe). Prices and available credit packages will be displayed in the purchase section. When initiating a purchase, the User will be redirected to the secure environment of the payment provider. MapMyLearn does not store the User's complete payment details." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Non-Refundable: Unless applicable law requires otherwise, purchased credits are non-refundable once consumed or allocated to the account." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Expiration and Changes: Currently, credits do not expire as long as the User's account remains active. However, we reserve the right to change the credit system, including introducing expiration dates or transitioning to a subscription model in the future. Any such changes will be communicated to users in advance in accordance with Section 9 (Modifications)." /></ListItem>
      </List>
      
      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        9. Availability, Modifications, and Termination of Service
      </Typography>
       <List dense>
        <ListItem><ListItemText primary="Availability: MapMyLearn strives to keep the Platform operational but does not guarantee uninterrupted or error-free access. Interruptions may occur due to maintenance, updates, or force majeure." /></ListItem>
        <ListItem><ListItemText primary="Modifications: We reserve the right to modify or discontinue, temporarily or permanently, the Service (or any part thereof, including credit costs) with or without notice. We may also modify these T&C periodically. Modifications will be effective upon their publication on the Platform or notification to the User. Continued use of the Service after a modification implies acceptance of the new terms." /></ListItem>
        <ListItem><ListItemText primary="Termination by User: The User may stop using the Service at any time. To request the deletion of their account and associated data, they must contact pablomiguelargudo@gmail.com from the registered email address." /></ListItem>
        <ListItem><ListItemText primary="Termination by MapMyLearn: We reserve the right to suspend or cancel a User's account and access to the Service if they breach these T&C, engage in fraudulent or illegal activities, or due to prolonged inactivity (e.g., 1 year), with prior notification if possible and legally required." /></ListItem>
      </List>
      
      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        10. Disclaimer of Warranties and Limitation of Liability
      </Typography>
       <List dense>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="AI Generated Content: The Service is provided 'as is' and 'as available'. MapMyLearn DOES NOT WARRANT that the generated content (text and audio) is accurate, complete, reliable, suitable for a particular purpose, up-to-date, or error-free. The User is solely responsible for verifying the information and using it at their own risk. Generated content does not substitute professional, academic, or expert advice." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Operation: We do not guarantee that the Service will meet the User's expectations or operate without interruptions or errors." /></ListItem>
        <ListItem sx={{ pl: 2 }}>
           <ListItemText 
                primary="Limitation of Liability: To the maximum extent permitted by law, Pablo Miguel Argudo shall not be liable for direct, indirect, incidental, special, consequential, or punitive damages (including, without limitation, loss of profits, data, use, goodwill, or other intangible losses) resulting from:" 
                secondary={
                    <List dense disablePadding sx={{ pl: 2 }}>
                        <ListItem sx={{ pl: 0, pt: 0 }}><ListItemText primary="Access to or use of, or the inability to access or use the Service." sx={{ m:0 }} /></ListItem>
                        <ListItem sx={{ pl: 0, pt: 0 }}><ListItemText primary="Any content obtained from the Service, especially that generated by AI." sx={{ m:0 }} /></ListItem>
                        <ListItem sx={{ pl: 0, pt: 0 }}><ListItemText primary="Unauthorized access, use, or alteration of User transmissions or content." sx={{ m:0 }} /></ListItem>
                        <ListItem sx={{ pl: 0, pt: 0 }}><ListItemText primary="Any other matter relating to the Service." sx={{ m:0 }} /></ListItem>
                   </List>
                } 
            />
        </ListItem>
        <ListItem><ListItemText primary="This limitation of liability shall not affect the consumer's non-waivable rights under Spanish law nor liability for willful misconduct or gross negligence by Pablo Miguel Argudo." /></ListItem>
      </List>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        11. Applicable Law and Jurisdiction
      </Typography>
      <Typography paragraph>
        These T&C shall be governed by and construed in accordance with the laws of Spain. For any dispute that may arise from accessing or using the Platform, the parties submit, expressly waiving any other jurisdiction that may correspond to them, to the Courts and Tribunals of the User's domicile (if they are a consumer residing in Spain) or to the Courts and Tribunals of Valencia, Spain (if the user is a company or non-resident in Spain acting as such).
      </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        12. Contact
      </Typography>
      <Typography paragraph>
        For any questions or inquiries about these T&C, you can contact us at: pablomiguelargudo@gmail.com.
      </Typography>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        13. Miscellaneous
      </Typography>
       <List dense>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Entire Agreement: These T&C, together with the Privacy Policy, constitute the entire agreement between the User and MapMyLearn." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="Severability: If any clause of these T&C is declared null or unenforceable, the remaining clauses shall remain in effect." /></ListItem>
        <ListItem sx={{ pl: 2 }}><ListItemText primary="No Waiver: The failure of MapMyLearn to exercise any right or provision of these T&C shall not constitute a waiver of such right or provision." /></ListItem>
      </List>

    </Container>
  );
};

export default TermsPage;

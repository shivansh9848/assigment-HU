# Research Appendix

## Product Request
Build a simple todo app

## URLs Consulted (Citations)
- https://medium.com/product-manager-journal/designing-a-simple-todo-app-b4d4ed9300a4
- https://www.appsmith.com/blog/low-code-buyers-guide-best-practices
- https://dzone.com/articles/11-best-practices-for-developing-secure-web-application
- https://www.incredibuild.com/blog/how-to-build-apps-faster-while-remaining-secure-compliant-a-devops-guide
- https://hyperproof.io/resource/secure-software-development-best-practices/
- https://www.legitsecurity.com/aspm-knowledge-base/web-application-security-requirements
- https://snyk.io/blog/application-security-best-practices/
- https://www.f5.com/company/blog/top-10-web-application-security-best-practices
- https://testomat.io/blog/edge-cases-in-software-development/
- https://flinthillsgroup.com/risks-limitations-of-ai-app-builders/
- https://medium.com/swlh/taking-the-edge-off-of-edge-cases-7b3008d83a57
- https://softwareengineering.stackexchange.com/questions/321650/acceptance-criteria-for-edge-cases
- https://bugroll.com/build-better-software-by-minimizing-risks-abe1e219f165
- https://www.virtuosoqa.com/post/edge-case-testing
- https://www.infoq.com/presentations/edge-benefits-limitations/
- https://avassa.io/articles/the-second-application-challenge-for-distributed-edge-clouds/

## Key Findings Summary
Build a simple todo app with secure authentication, input validation, and regular updates. Use best practices like encryption and secure coding. Prioritize performance and security compliance.

Risks include data security, limited scalability, and poor code quality. Constraints involve time, budget, and resource limitations. Edge cases include handling empty inputs and unexpected data formats.

## How Research Impacts Decisions
This research is persisted as a first-class artifact and is intended to inform downstream epic/story/spec decisions. Examples: confirming best-practice security guidance, identifying common feature expectations, and surfacing risks/constraints. When generating epics/stories, we will cite these URLs and justify choices (the 'why X was chosen' requirement).

## Raw Search Notes
```json
{
  "searches": [
    {
      "query": "Best practices, security, and common requirements for: Build a simple todo app",
      "answer": "Build a simple todo app with secure authentication, input validation, and regular updates. Use best practices like encryption and secure coding. Prioritize performance and security compliance.",
      "results": [
        {
          "title": "Designing a Simple Todo App",
          "url": "https://medium.com/product-manager-journal/designing-a-simple-todo-app-b4d4ed9300a4",
          "score": 0.9974491,
          "content": "# Designing a Simple Todo App. Keeping it simple, yet effective. The app store, be it Apple or Google, is filled with a lot of todo apps trying to help you achieve success. My favorite todo apps are Clear and Google Keep. As an exercise, I decided to explore the idea of designing my own todo app. App should help the users stay in focus, manage and complete their todos effectively. While having a clear focus will help users get there, the app’s model should help users ultimately get things done. To keep things simple, I decided to follow Material Design to build Taskky app than trying to introduce new UX paradigms. * Just because you did not complete today, doesn’t mean it becomes a todo to complete tomorrow or someday. Tap on the + round button to add todo for today, tomorrow and someday respectively. This is no where perfect but I feel with its unique approach of managing todos, Taskky can help you be productive."
        },
        {
          "title": "18 Best Practices to Develop Secure, Performant Web Applications ...",
          "url": "https://www.appsmith.com/blog/low-code-buyers-guide-best-practices",
          "score": 0.9588471,
          "content": "In this post, we cover the eighteen best practices you need to build performant and secure apps with low code so that you can take full advantage of low-code"
        },
        {
          "title": "11 Best Practices for Developing Secure Web Applications - DZone",
          "url": "https://dzone.com/articles/11-best-practices-for-developing-secure-web-application",
          "score": 0.91964257,
          "content": "Follow these 11 best practices to build secure web applications, including input validation, encryption, secure authentication, and regular security updates."
        },
        {
          "title": "How to build apps faster while remaining secure/compliant",
          "url": "https://www.incredibuild.com/blog/how-to-build-apps-faster-while-remaining-secure-compliant-a-devops-guide",
          "score": 0.8962514,
          "content": "We'll also discuss how IncrediBuild can help you deliver high-quality and secure applications faster without sacrificing DevOps compliance."
        },
        {
          "title": "Secure Software Development | Hyperproof | [Best Practices]",
          "url": "https://hyperproof.io/resource/secure-software-development-best-practices/",
          "score": 0.8031738,
          "content": "This article will discuss best practices and frameworks for building secure software and how to identify and respond to vulnerabilities early in the"
        },
        {
          "title": "Web Application Security Requirements and Best Practices",
          "url": "https://www.legitsecurity.com/aspm-knowledge-base/web-application-security-requirements",
          "score": 0.48242912,
          "content": "* Web Application Security Requirements and Best Practices. # Web Application Security Requirements and Best Practices. Understanding web application security requirements helps you put the right practices in place to protect applications, employees, and customers alike. ## Web Application Security Definition. Web application security refers to the measures developers and companies take to protect apps from malicious attacks. Businesses can also protect sensitive information and build credibility by prioritizing web application security standards, like Open Worldwide Application Security Project (OWSAP) guidelines. ## Key Web Application Security Requirements. Applications must validate all user input and block harmful data to prevent attacks like SQL injection and cross-site scripting (XSS). ## Web Application Security Best Practices. Learning how to secure web applications requires you to address potential threats from every angle. Use security tools that verify a user is human, like CAPTCHA or other verification systems, to block automated bots that try to exploit your application."
        },
        {
          "title": "15 Application Security Best Practices - Snyk",
          "url": "https://snyk.io/blog/application-security-best-practices/",
          "score": 0.39420095,
          "content": "Create a list of all assets that require protection. · Identify your threats and how to isolate and contain them. · Identify attack vectors that"
        },
        {
          "title": "Top 10 Web Application Security Best Practices - F5",
          "url": "https://www.f5.com/company/blog/top-10-web-application-security-best-practices",
          "score": 0.09138211,
          "content": "* **Protection**: Implement real-time, in-line security controls such as web application firewalls (WAFs), rate limiting, sensitive data masking, and API-specific protection rules to enforce policy, mitigate malicious or unwanted activity (including automated threats), and prevent the exposure of sensitive data via APIs. As applications become more decentralized and attackers more sophisticated, it’s increasing critical to implement a complete web application and API protection (WAAP) solution for robust web app protection and to simplify security operations across complex application environments. Key benefits of a WAAP include centralized security policy management to enable consistent protection across all environments, regardless of deployment architecture or location, along with a unified set of security controls for both applications and APIs. A WAAP also delivers improved visibility and anomaly detection across the entire threat landscape, with detailed audit trails and event correlation to support regulatory compliance and incident response. ### Web application and API security from F5. The F5 Application Delivery and Security Platform converges the critical services required for ensuring every web app, API, and the underlying infrastructure—from the edge to the cloud—has consistent, comprehensive security, high availability, and intelligent orchestration for the most intensive workloads."
        }
      ]
    },
    {
      "query": "Risks, constraints, and edge cases for: Build a simple todo app",
      "answer": "Risks include data security, limited scalability, and poor code quality. Constraints involve time, budget, and resource limitations. Edge cases include handling empty inputs and unexpected data formats.",
      "results": [
        {
          "title": "Edge Cases in Software Development: Guide to Testing - Testomat.io",
          "url": "https://testomat.io/blog/edge-cases-in-software-development/",
          "score": 0.96378,
          "content": "An edge case is a problem that can occur when a software program pushes its limits. This can make the program behave in surprising ways or even cause it to"
        },
        {
          "title": "Risks & Limitations Of AI App Builders - Flint Hills Group",
          "url": "https://flinthillsgroup.com/risks-limitations-of-ai-app-builders/",
          "score": 0.9219218,
          "content": "Lack of Full Customization · Creates Dependency · Data Security and Privacy Concerns · Limited Scalability · Quality of Code and Performance Issues."
        },
        {
          "title": "Taking the Edge off of Edge Cases | by Sara Khandaker - Medium",
          "url": "https://medium.com/swlh/taking-the-edge-off-of-edge-cases-7b3008d83a57",
          "score": 0.8322367,
          "content": "## Identifying Edge Cases in Algorithms and Applications. Edge cases are the worst! ## What is an Edge Case? We like the happy path; we don't like the edge cases. So, why is it important to think about edge cases? Whether it's an application or simply an algorithm during a technical interview, thinking about edge cases will create a more robust end product. So how do we find these pesky edge cases? Identifying edge cases is still largely done by humans. When do we look for these edge cases? Planning properly during the development phase can help identify many important edge cases. Remember to ask lots of clarifying questions and always step through your code with examples and edge cases. Make sure your solution holds up to the edge cases considered. ## How to Fix Edge Cases? So now how do we fix the edge cases we just identified? You do not have to and nor should you support every edge case."
        },
        {
          "title": "Acceptance Criteria for Edge Cases",
          "url": "https://softwareengineering.stackexchange.com/questions/321650/acceptance-criteria-for-edge-cases",
          "score": 0.70416015,
          "content": "He says its unfair since I don't specify the edge cases and how the program should respond in the acceptance criteria, as he tends to code for only what I describe in the story. In the ideal SCRUM world, would it be incumbent on me to add a \"handle divide by zero scenario\" to the acceptance criteria or should he be working through those cases as he develops so the app doesn't implode on 5/0? QA please update your acceptance criteria for this scenario, we don't need an additional story for this. The team can still accept the original story as it is meeting all the original requirements, and then pick up the spike story in the next iteration. * Suggest that the dev include time in the story to the cover fixing discovered edge cases. Detail of acceptance criteria in user story. 3\") Agile User Stories and acceptance criteria. 2\") Defining acceptance criteria for a user story. Common details in the acceptance criteria of related user stories."
        },
        {
          "title": "Build Better Software by Minimizing Risks | by Brad Bollenbach",
          "url": "https://bugroll.com/build-better-software-by-minimizing-risks-abe1e219f165",
          "score": 0.6808786,
          "content": "Quantifying Risk Makes for Better Code. There are usually only a small handful of core ingredients behind what we do: a database, some CRUD"
        },
        {
          "title": "Edge Case Testing Explained – What to Test & How to Do It",
          "url": "https://www.virtuosoqa.com/post/edge-case-testing",
          "score": 0.43974736,
          "content": "Edge case testing is a QA methodology focused on validating software behavior at operational boundaries, input extremes, and unlikely"
        },
        {
          "title": "Building Applications from Edge to Cloud - InfoQ",
          "url": "https://www.infoq.com/presentations/edge-benefits-limitations/",
          "score": 0.16776335,
          "content": "The panelists discuss the benefits and limitations of edge technologies and how to adopt them in existing applications and deployments."
        },
        {
          "title": "Avoiding Edge Silos: The Second Application Challenge - Avassa",
          "url": "https://avassa.io/articles/the-second-application-challenge-for-distributed-edge-clouds/",
          "score": 0.009376238,
          "content": "Explore why the second edge application poses major challenges in edge computing, and how to scale deployments effectively without vendor lock-in."
        }
      ]
    }
  ]
}
```
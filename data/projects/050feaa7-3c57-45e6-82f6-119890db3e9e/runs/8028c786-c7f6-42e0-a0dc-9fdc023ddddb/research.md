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
- https://flinthillsgroup.com/risks-limitations-of-ai-app-builders/
- https://testomat.io/blog/edge-cases-in-software-development/
- https://www.virtuosoqa.com/post/edge-case-testing
- https://distillery.com/blog/custom-app-development-risks/
- https://medium.com/swlh/taking-the-edge-off-of-edge-cases-7b3008d83a57
- https://www.nngroup.com/articles/strategies-complex-application-design/
- https://www.brightscout.com/insight/what-are-the-key-challenges-in-app-development-projects-and-how-to-overcome-them
- https://softwareengineering.stackexchange.com/questions/321650/acceptance-criteria-for-edge-cases

## Key Findings Summary
To build a simple todo app, use secure authentication, input validation, and encryption. Follow best practices for secure software development and ensure regular updates to address vulnerabilities.

Risks include data security, limited scalability, and poor code quality. Constraints involve time, budget, and feature scope. Edge cases involve unusual inputs or conditions.

## How Research Impacts Decisions
This research is persisted as a first-class artifact and is intended to inform downstream epic/story/spec decisions. Examples: confirming best-practice security guidance, identifying common feature expectations, and surfacing risks/constraints. When generating epics/stories, we will cite these URLs and justify choices (the 'why X was chosen' requirement).

## Raw Search Notes
```json
{
  "searches": [
    {
      "query": "Best practices, security, and common requirements for: Build a simple todo app",
      "answer": "To build a simple todo app, use secure authentication, input validation, and encryption. Follow best practices for secure software development and ensure regular updates to address vulnerabilities.",
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
      "answer": "Risks include data security, limited scalability, and poor code quality. Constraints involve time, budget, and feature scope. Edge cases involve unusual inputs or conditions.",
      "results": [
        {
          "title": "Risks & Limitations Of AI App Builders",
          "url": "https://flinthillsgroup.com/risks-limitations-of-ai-app-builders/",
          "score": 0.2598801,
          "content": "Lack of Full Customization · Creates Dependency · Data Security and Privacy Concerns · Limited Scalability · Quality of Code and Performance Issues."
        },
        {
          "title": "Edge Cases in Software Development: Guide to Testing",
          "url": "https://testomat.io/blog/edge-cases-in-software-development/",
          "score": 0.2590849,
          "content": "An edge case is a problem that can occur when a software program pushes its limits. This can make the program behave in surprising ways or even cause it to"
        },
        {
          "title": "Edge Case Testing Explained – What to Test & How to Do It",
          "url": "https://www.virtuosoqa.com/post/edge-case-testing",
          "score": 0.1560666,
          "content": "Edge case testing is a QA methodology focused on validating software behavior at operational boundaries, input extremes, and unlikely"
        },
        {
          "title": "Custom App Development: 7 Risks to Avoid - Distillery",
          "url": "https://distillery.com/blog/custom-app-development-risks/",
          "score": 0.10748451,
          "content": "In this article, we provide an overview of key risks to understand when embarking on a custom application development project."
        },
        {
          "title": "Taking the Edge off of Edge Cases | by Sara Khandaker",
          "url": "https://medium.com/swlh/taking-the-edge-off-of-edge-cases-7b3008d83a57",
          "score": 0.107315995,
          "content": "## Identifying Edge Cases in Algorithms and Applications. Edge cases are the worst! ## What is an Edge Case? We like the happy path; we don't like the edge cases. So, why is it important to think about edge cases? Whether it's an application or simply an algorithm during a technical interview, thinking about edge cases will create a more robust end product. So how do we find these pesky edge cases? Identifying edge cases is still largely done by humans. When do we look for these edge cases? Planning properly during the development phase can help identify many important edge cases. Remember to ask lots of clarifying questions and always step through your code with examples and edge cases. Make sure your solution holds up to the edge cases considered. ## How to Fix Edge Cases? So now how do we fix the edge cases we just identified? You do not have to and nor should you support every edge case."
        },
        {
          "title": "UX Strategies for Complex-Application Design",
          "url": "https://www.nngroup.com/articles/strategies-complex-application-design/",
          "score": 0.106421195,
          "content": "Expert users and domain partners can collaborate in cocreation and evaluation, helping interpret edge cases, flag unseen risks, or point out"
        },
        {
          "title": "What are the Key Challenges in App Development Projects ...",
          "url": "https://www.brightscout.com/insight/what-are-the-key-challenges-in-app-development-projects-and-how-to-overcome-them",
          "score": 0.09077596,
          "content": "# What are the Key Challenges in App Development Projects and How to Overcome Them? The development of mobile applications comes with its own set of challenges, especially in a competitive market, from navigating technical complexities to meeting user expectations. Common challenges in app development projects include scope creep, unclear requirements, tight deadlines, and budget constraints. Test each potential feature against your app's main purpose and target user persona. Remove features that don't clearly solve your users' challenges. Whether it’s tackling moving goalposts, avoiding feature bloat, or ensuring you’re building something people truly want, the key lies in proactive planning, clear communication, and a relentless focus on user value. By addressing challenges like cross-platform compatibility, performance optimization, and security concerns with strategic solutions, you set the stage for an app that’s not only functional but also future-ready. And when you integrate flexibility, user-centric design, and continuous learning into your development approach, you create a foundation that can adapt to change, deliver impact, and thrive in a competitive landscape."
        },
        {
          "title": "Acceptance Criteria for Edge Cases",
          "url": "https://softwareengineering.stackexchange.com/questions/321650/acceptance-criteria-for-edge-cases",
          "score": 0.05958685,
          "content": "He says its unfair since I don't specify the edge cases and how the program should respond in the acceptance criteria, as he tends to code for only what I describe in the story. In the ideal SCRUM world, would it be incumbent on me to add a \"handle divide by zero scenario\" to the acceptance criteria or should he be working through those cases as he develops so the app doesn't implode on 5/0? QA please update your acceptance criteria for this scenario, we don't need an additional story for this. The team can still accept the original story as it is meeting all the original requirements, and then pick up the spike story in the next iteration. * Suggest that the dev include time in the story to the cover fixing discovered edge cases. Detail of acceptance criteria in user story. 3\") Agile User Stories and acceptance criteria. 2\") Defining acceptance criteria for a user story. Common details in the acceptance criteria of related user stories."
        }
      ]
    }
  ]
}
```
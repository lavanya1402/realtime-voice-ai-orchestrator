flowchart TD

    %% ========= NODES =========
    A["📞 User Calls Twilio Number<br/>+1 507 936 5391"] 
    B["☁️ Twilio Voice Webhook<br/>/voice"]
    C["🚀 FastAPI Server"]
    D["🔌 Twilio Media Stream<br/>WebSocket"]
    E["🎙️ FastAPI /media<br/>WebSocket Endpoint"]
    F["🧠 Deepgram Live API<br/>Streaming STT"]
    G["📝 Real-Time Transcript Output"]

    %% ========= FLOW =========
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G

    %% ========= PASTEL COLORS =========
    classDef caller fill:#FDE2E4,stroke:#E5989B,color:#333,stroke-width:2px;
    classDef twilio fill:#FFF1E6,stroke:#F4A261,color:#333,stroke-width:2px;
    classDef server fill:#E3F2FD,stroke:#64B5F6,color:#333,stroke-width:2px;
    classDef ws fill:#E8F5E9,stroke:#81C784,color:#333,stroke-width:2px;
    classDef deepgram fill:#F3E5F5,stroke:#BA68C8,color:#333,stroke-width:2px;
    classDef output fill:#FFF9C4,stroke:#FBC02D,color:#333,stroke-width:2px;

    class A caller
    class B,D twilio
    class C,E server
    class F deepgram
    class G output
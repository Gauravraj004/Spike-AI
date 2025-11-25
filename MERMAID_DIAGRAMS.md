graph TB
    subgraph Input
        A[Screenshot PNG]
        B[HTML Source]
    end

    subgraph "Local Analysis"
        C[HTML Parser<br/>BeautifulSoup]
        C --> C1[Check Element Count]
        C --> C2[Detect Frameworks]
        C --> C3[Find Modals/Loading]
        C --> C4[Analyze Scripts]
        C1 & C2 & C3 & C4 --> C5[Generate Capture<br/>Recommendations]
    end

    subgraph "Cloud Analysis"
        D[GPT-4o Vision API]
        D --> D1[Visual Diagnosis]
        D --> D2[Capture Improvement<br/>Suggestions]
    end

    subgraph Output
        E1[JSON<br/>Full Details]
        E2[CSV<br/>All Fields]
        E3[Console<br/>Top 3 Issues]
    end

    A --> D
    B --> C
    C5 --> D
    D1 --> E1
    D1 --> E2
    D2 --> E1
    D2 --> E2
    C5 --> E3
    D2 --> E3

    style C5 fill:#ffeb3b
    style D2 fill:#ffeb3b
    style E1 fill:#e8f5e9
    style E2 fill:#e8f5e9
    style E3 fill:#e8f5e9

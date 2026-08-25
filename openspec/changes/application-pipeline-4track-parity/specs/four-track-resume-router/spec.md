## Purpose

Provides an automated job taxonomy classifier and synthesis engine that maps incoming positions to four engineering tracks (Control, Automation/Embedded, Mechatronics, Mechanical/CFD) and generates targeted outreach greetings and resume attachments.

## ADDED Requirements

### Requirement: 4-Track Job Classification
The router SHALL analyze job titles and descriptions to classify positions into exactly one of four distinct engineering tracks: `control` (控制算法), `embedded_auto` (自动化与嵌入式), `mechatronics` (机电一体化与电气), or `mechanical_cfd` (机械结构与仿真).

#### Scenario: Classifying control algorithm role
- **WHEN** job title contains "MPC" or "运动控制算法"
- **THEN** system assigns the track `control` with badge `🔵 控制算法`

#### Scenario: Classifying embedded automation role
- **WHEN** job title contains "STM32" or "固件开发" or "嵌入式软件"
- **THEN** system assigns the track `embedded_auto` with badge `🟣 自动化与嵌入式`

#### Scenario: Classifying mechatronics role
- **WHEN** job title contains "EPLAN" or "电气工程师" or "机电一体化"
- **THEN** system assigns the track `mechatronics` with badge `🟢 机电一体化与电气`

#### Scenario: Classifying mechanical CFD role
- **WHEN** job title contains "结构设计" or "CFD" or "Fluent" or "有限元仿真"
- **THEN** system assigns the track `mechanical_cfd` with badge `🟠 机械结构与仿真`

### Requirement: Dynamic Greeting Synthesis and Resume Binding
The router SHALL synthesize customized candidate introduction copy and dynamically resolve the absolute file path for the recommended PDF resume asset corresponding to the matched track.

#### Scenario: Generating track greeting script
- **WHEN** router evaluates a position in the `control` track
- **THEN** the system generates a greeting copy highlighting state-space modeling, EKF filtering, and EI publication / patent credentials

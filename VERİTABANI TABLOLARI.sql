/*CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Email NVARCHAR(100) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    Phone NVARCHAR(20),
    IsActive BIT DEFAULT 1
);

CREATE TABLE Citizens (
    UserID INT PRIMARY KEY,
    NationalID CHAR(11) NOT NULL UNIQUE,
    DateOfBirth DATE NOT NULL
);

CREATE TABLE Doctors (
    UserID INT PRIMARY KEY,
    Specialty NVARCHAR(100) NOT NULL,
    DiplomaNumber NVARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE HospitalManagers (
    UserID INT PRIMARY KEY
);

CREATE TABLE SystemManagers (
    UserID INT PRIMARY KEY
);

CREATE TABLE Hospitals (
    HospitalID INT IDENTITY(1,1) PRIMARY KEY,
    HospitalName NVARCHAR(150) NOT NULL,
    Address NVARCHAR(250) NOT NULL,
    Phone NVARCHAR(20),
    IsActive BIT DEFAULT 1
);

CREATE TABLE Provinces (
    ProvinceID INT IDENTITY(1,1) PRIMARY KEY,
    ProvinceName NVARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Districts (
    DistrictID INT IDENTITY(1,1) PRIMARY KEY,
    DistrictName NVARCHAR(50) NOT NULL
);

CREATE TABLE Clinics (
    ClinicID INT IDENTITY(1,1) PRIMARY KEY,
    ClinicName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(250)
);

CREATE TABLE DoctorAssignments (
    AssignmentID INT IDENTITY(1,1) PRIMARY KEY,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    WorkDay NVARCHAR(20) NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,

    CHECK (EndDate >= StartDate),
    CHECK (EndTime > StartTime)
);

CREATE TABLE WorkSchedules (
    ScheduleID INT IDENTITY(1,1) PRIMARY KEY,
    Day NVARCHAR(20) NOT NULL,
    StartTime TIME,
    EndTime TIME,
    BreakStartTime TIME,
    BreakEndTime TIME,
    IsClosed BIT DEFAULT 0
);

CREATE TABLE AvailabilitySlots (
    SlotID INT IDENTITY(1,1) PRIMARY KEY,
    SlotDate DATE NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    Capacity INT NOT NULL,
    FilledCapacity INT DEFAULT 0,
    IsAvailable BIT DEFAULT 1,

    CHECK (EndTime > StartTime),
    CHECK (Capacity > 0),
    CHECK (FilledCapacity >= 0 AND FilledCapacity <= Capacity)
);

CREATE TABLE Appointments (
    AppointmentID INT IDENTITY(1,1) PRIMARY KEY,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    Status NVARCHAR(30) NOT NULL,
    CancellationReason NVARCHAR(250)
);

CREATE TABLE Notifications (
    NotificationID INT IDENTITY(1,1) PRIMARY KEY,
    Message NVARCHAR(500) NOT NULL,
    NotificationDate DATETIME2 DEFAULT GETDATE(),
    NotificationType NVARCHAR(50),
    IsRead BIT DEFAULT 0
);

CREATE TABLE WaitingListRequests (
    RequestID INT IDENTITY(1,1) PRIMARY KEY,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    PreferredStartDate DATE NOT NULL,
    PreferredEndDate DATE NOT NULL,
    Status NVARCHAR(30) NOT NULL,

    CHECK (PreferredEndDate >= PreferredStartDate)
);

CREATE TABLE AuditLogs (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    ActionType NVARCHAR(100) NOT NULL,
    ActionDate DATETIME2 DEFAULT GETDATE(),
    Description NVARCHAR(500)
);
*/
ALTER TABLE Citizens
ADD CONSTRAINT FK_Citizens_Users
FOREIGN KEY (UserID) REFERENCES Users(UserID);

ALTER TABLE Doctors
ADD CONSTRAINT FK_Doctors_Users
FOREIGN KEY (UserID) REFERENCES Users(UserID);

ALTER TABLE HospitalManagers
ADD CONSTRAINT FK_HospitalManagers_Users
FOREIGN KEY (UserID) REFERENCES Users(UserID);

ALTER TABLE SystemManagers
ADD CONSTRAINT FK_SystemManagers_Users
FOREIGN KEY (UserID) REFERENCES Users(UserID);

ALTER TABLE Districts
ADD ProvinceID INT NOT NULL;

ALTER TABLE Hospitals
ADD DistrictID INT NOT NULL;

ALTER TABLE Clinics
ADD HospitalID INT NOT NULL;

ALTER TABLE Districts
ADD CONSTRAINT FK_Districts_Provinces
FOREIGN KEY (ProvinceID) REFERENCES Provinces(ProvinceID);

ALTER TABLE Hospitals
ADD CONSTRAINT FK_Hospitals_Districts
FOREIGN KEY (DistrictID) REFERENCES Districts(DistrictID);

ALTER TABLE Clinics
ADD CONSTRAINT FK_Clinics_Hospitals
FOREIGN KEY (HospitalID) REFERENCES Hospitals(HospitalID);

ALTER TABLE DoctorAssignments
ADD DoctorID INT NOT NULL,
    ClinicID INT NOT NULL;

ALTER TABLE DoctorAssignments
ADD CONSTRAINT FK_DoctorAssignments_Doctors
FOREIGN KEY (DoctorID) REFERENCES Doctors(UserID);

ALTER TABLE DoctorAssignments
ADD CONSTRAINT FK_DoctorAssignments_Clinics
FOREIGN KEY (ClinicID) REFERENCES Clinics(ClinicID);

ALTER TABLE WorkSchedules
ADD AssignmentID INT NOT NULL;

ALTER TABLE WorkSchedules
ADD CONSTRAINT FK_WorkSchedules_DoctorAssignments
FOREIGN KEY (AssignmentID)
REFERENCES DoctorAssignments(AssignmentID);

ALTER TABLE AvailabilitySlots
ADD ScheduleID INT NOT NULL;

ALTER TABLE AvailabilitySlots
ADD CONSTRAINT FK_AvailabilitySlots_WorkSchedules
FOREIGN KEY (ScheduleID)
REFERENCES WorkSchedules(ScheduleID);

ALTER TABLE Appointments
ADD CitizenUserID INT NOT NULL,
    SlotID INT NOT NULL;

ALTER TABLE Appointments
ADD CONSTRAINT FK_Appointments_Citizens
FOREIGN KEY (CitizenUserID)
REFERENCES Citizens(UserID);

ALTER TABLE Appointments
ADD CONSTRAINT FK_Appointments_AvailabilitySlots
FOREIGN KEY (SlotID)
REFERENCES AvailabilitySlots(SlotID);

ALTER TABLE Notifications
ADD UserID INT NOT NULL,
    AppointmentID INT NULL,
    RequestID INT NULL;

ALTER TABLE Notifications
ADD CONSTRAINT FK_Notifications_Users
FOREIGN KEY (UserID) REFERENCES Users(UserID);

ALTER TABLE Notifications
ADD CONSTRAINT FK_Notifications_Appointments
FOREIGN KEY (AppointmentID)
REFERENCES Appointments(AppointmentID);

ALTER TABLE WaitingListRequests
ADD CitizenUserID INT NOT NULL,
    ClinicID INT NOT NULL,
    DoctorID INT NULL;

ALTER TABLE WaitingListRequests
ADD CONSTRAINT FK_WaitingListRequests_Citizens
FOREIGN KEY (CitizenUserID)
REFERENCES Citizens(UserID);

ALTER TABLE WaitingListRequests
ADD CONSTRAINT FK_WaitingListRequests_Clinics
FOREIGN KEY (ClinicID)
REFERENCES Clinics(ClinicID);

ALTER TABLE WaitingListRequests
ADD CONSTRAINT FK_WaitingListRequests_Doctors
FOREIGN KEY (DoctorID)
REFERENCES Doctors(UserID);

ALTER TABLE Notifications
ADD CONSTRAINT FK_Notifications_WaitingListRequests
FOREIGN KEY (RequestID)
REFERENCES WaitingListRequests(RequestID);

ALTER TABLE AuditLogs
ADD UserID INT NOT NULL;

ALTER TABLE AuditLogs
ADD CONSTRAINT FK_AuditLogs_Users
FOREIGN KEY (UserID)
REFERENCES Users(UserID);


INSERT INTO Users
(FirstName, LastName, Email, PasswordHash, Phone, IsActive)
VALUES
('Ayse', 'Yilmaz', 'ayse@gmail.com', 'DEMO_HASH_001', '05551111111', 1),
('Mehmet', 'Demir', 'mehmet@gmail.com', 'DEMO_HASH_002', '05552222222', 1),
('Zeynep', 'Kaya', 'zeynep@gmail.com', 'DEMO_HASH_003', '05553333333', 1),
('Ali', 'Celik', 'ali@gmail.com', 'DEMO_HASH_004', '05554444444', 1),
('Elif', 'Sahin', 'elif@gmail.com', 'DEMO_HASH_005', '05555555555', 1),

('Dr.Ahmet', 'Yildiz', 'ahmet.doctor@mhrs.com', 'DEMO_HASH_006', '05556666666', 1),
('Dr.Selin', 'Arslan', 'selin.doctor@mhrs.com', 'DEMO_HASH_007', '05557777777', 1),
('Dr.Can', 'Aydin', 'can.doctor@mhrs.com', 'DEMO_HASH_008', '05558888888', 1),

('Fatma', 'Kurt', 'manager@mhrs.com', 'DEMO_HASH_009', '05559999999', 1),
('Admin', 'User', 'admin@mhrs.com', 'DEMO_HASH_010', '05550000000', 1);

INSERT INTO Citizens (UserID, NationalID, DateOfBirth)
SELECT UserID, NationalID, DateOfBirth
FROM (
    SELECT 'ayse@gmail.com' AS Email, '10000000001' AS NationalID, '1998-04-12' AS DateOfBirth
    UNION ALL SELECT 'mehmet@gmail.com', '10000000002', '1995-08-21'
    UNION ALL SELECT 'zeynep@gmail.com', '10000000003', '2001-02-15'
    UNION ALL SELECT 'ali@gmail.com', '10000000004', '1989-11-03'
    UNION ALL SELECT 'elif@gmail.com', '10000000005', '2003-06-27'
) AS C
INNER JOIN Users U ON U.Email = C.Email;


INSERT INTO Doctors (UserID, Specialty, DiplomaNumber)
SELECT UserID, Specialty, DiplomaNumber
FROM (
    SELECT 'ahmet.doctor@mhrs.com' AS Email,
           'Cardiology' AS Specialty,
           'DIP1001' AS DiplomaNumber
    UNION ALL
    SELECT 'selin.doctor@mhrs.com',
           'Neurology',
           'DIP1002'
    UNION ALL
    SELECT 'can.doctor@mhrs.com',
           'Pediatrics',
           'DIP1003'
) D
INNER JOIN Users U ON U.Email = D.Email;

INSERT INTO HospitalManagers (UserID)
SELECT UserID
FROM Users
WHERE Email = 'manager@mhrs.com';

INSERT INTO SystemManagers (UserID)
SELECT UserID
FROM Users
WHERE Email = 'admin@mhrs.com';

INSERT INTO Provinces (ProvinceName)
VALUES
('Istanbul'),
('Ankara'),
('Izmir');

INSERT INTO Districts (DistrictName, ProvinceID)
SELECT D.DistrictName, P.ProvinceID
FROM (
    SELECT 'Kadikoy' AS DistrictName, 'Istanbul' AS ProvinceName
    UNION ALL SELECT 'Besiktas', 'Istanbul'
    UNION ALL SELECT 'Cankaya', 'Ankara'
    UNION ALL SELECT 'Kecioren', 'Ankara'
    UNION ALL SELECT 'Bornova', 'Izmir'
) D
INNER JOIN Provinces P
ON P.ProvinceName = D.ProvinceName;


INSERT INTO Hospitals
(HospitalName, Address, Phone, IsActive, DistrictID)

SELECT
    H.HospitalName,
    H.Address,
    H.Phone,
    1,
    D.DistrictID

FROM (
    SELECT
        'Istanbul City Hospital' AS HospitalName,
        'Besiktas, Istanbul' AS Address,
        '02120000001' AS Phone,
        'Besiktas' AS DistrictName

    UNION ALL

    SELECT
        'Kadikoy State Hospital',
        'Kadikoy, Istanbul',
        '02120000002',
        'Kadikoy'

    UNION ALL

    SELECT
        'Ankara Central Hospital',
        'Cankaya, Ankara',
        '03120000001',
        'Cankaya'

    UNION ALL

    SELECT
        'Izmir Ege Hospital',
        'Bornova, Izmir',
        '02320000001',
        'Bornova'
) H

INNER JOIN Districts D
ON D.DistrictName = H.DistrictName;


INSERT INTO Clinics (ClinicName, Description, HospitalID)
SELECT C.ClinicName, C.Description, H.HospitalID
FROM (
    SELECT 'Cardiology' AS ClinicName,
           'Heart and cardiovascular diseases' AS Description,
           'Istanbul City Hospital' AS HospitalName

    UNION ALL
    SELECT 'Neurology',
           'Brain and nervous system diseases',
           'Istanbul City Hospital'

    UNION ALL
    SELECT 'Dermatology',
           'Skin diseases',
           'Istanbul City Hospital'

    UNION ALL
    SELECT 'Pediatrics',
           'Child health and diseases',
           'Ankara Central Hospital'

    UNION ALL
    SELECT 'Orthopedics',
           'Bone and joint diseases',
           'Ankara Central Hospital'

    UNION ALL
    SELECT 'Cardiology',
           'Heart diseases',
           'Izmir Ege Hospital'

    UNION ALL
    SELECT 'ENT',
           'Ear nose and throat diseases',
           'Izmir Ege Hospital'
) C
INNER JOIN Hospitals H
ON H.HospitalName = C.HospitalName;

INSERT INTO DoctorAssignments
(StartDate, EndDate, WorkDay, StartTime, EndTime, DoctorID, ClinicID)

SELECT
    DATEADD(DAY, -30, CAST(GETDATE() AS DATE)),
    DATEADD(DAY, 90, CAST(GETDATE() AS DATE)),
    A.WorkDay,
    A.StartTime,
    A.EndTime,
    U.UserID,
    C.ClinicID

FROM (
    SELECT 'ahmet.doctor@mhrs.com' AS Email,
           'Cardiology' AS ClinicName,
           'Istanbul City Hospital' AS HospitalName,
           'Monday' AS WorkDay,
           CAST('09:00' AS TIME) AS StartTime,
           CAST('17:00' AS TIME) AS EndTime

    UNION ALL
    SELECT 'selin.doctor@mhrs.com',
           'Neurology',
           'Istanbul City Hospital',
           'Tuesday',
           '09:00',
           '17:00'

    UNION ALL
    SELECT 'can.doctor@mhrs.com',
           'Pediatrics',
           'Ankara Central Hospital',
           'Wednesday',
           '08:00',
           '16:00'

    UNION ALL
    SELECT 'ahmet.doctor@mhrs.com',
           'Cardiology',
           'Izmir Ege Hospital',
           'Thursday',
           '09:00',
           '17:00'

    UNION ALL
    SELECT 'selin.doctor@mhrs.com',
           'Dermatology',
           'Istanbul City Hospital',
           'Friday',
           '10:00',
           '18:00'
) A
INNER JOIN Users U ON U.Email = A.Email
INNER JOIN Clinics C
    ON C.ClinicName = A.ClinicName
INNER JOIN Hospitals H
    ON H.HospitalID = C.HospitalID
    AND H.HospitalName = A.HospitalName;

    INSERT INTO WorkSchedules
([Day], StartTime, EndTime, BreakStartTime, BreakEndTime, IsClosed, AssignmentID)

SELECT
    A.WorkDay,
    '09:00',
    '17:00',
    '12:00',
    '13:00',
    0,
    A.AssignmentID

FROM DoctorAssignments A
INNER JOIN Doctors D ON D.UserID = A.DoctorID
INNER JOIN Users U ON U.UserID = D.UserID
INNER JOIN Clinics C ON C.ClinicID = A.ClinicID

WHERE
    (U.Email = 'ahmet.doctor@mhrs.com' AND C.ClinicName = 'Cardiology')
    OR (U.Email = 'selin.doctor@mhrs.com' AND C.ClinicName = 'Neurology')
    OR (U.Email = 'can.doctor@mhrs.com' AND C.ClinicName = 'Pediatrics')
    OR (U.Email = 'ahmet.doctor@mhrs.com' AND C.ClinicName = 'Cardiology' AND A.WorkDay = 'Thursday')
    OR (U.Email = 'selin.doctor@mhrs.com' AND C.ClinicName = 'Dermatology');

    INSERT INTO AvailabilitySlots
(SlotDate, StartTime, EndTime, Capacity, FilledCapacity, IsAvailable, ScheduleID)

SELECT
    DATEADD(DAY, V.DayOffset, CAST(GETDATE() AS DATE)),
    V.StartTime,
    V.EndTime,
    2,
    0,
    1,
    W.ScheduleID

FROM WorkSchedules W

CROSS APPLY (
    VALUES
        (1, CAST('09:00' AS TIME), CAST('10:00' AS TIME)),
        (2, CAST('10:00' AS TIME), CAST('11:00' AS TIME)),
        (3, CAST('11:00' AS TIME), CAST('12:00' AS TIME))
) V(DayOffset, StartTime, EndTime);

INSERT INTO Appointments
(CreatedAt, Status, CancellationReason, CitizenUserID, SlotID)

SELECT
    GETDATE(),
    A.Status,
    A.CancellationReason,
    Citizen.UserID,
    S.SlotID

FROM (
    SELECT 'ayse@gmail.com' AS CitizenEmail,
           'ahmet.doctor@mhrs.com' AS DoctorEmail,
           'Istanbul City Hospital' AS HospitalName,
           'Cardiology' AS ClinicName,
           1 AS DayOffset,
           CAST('09:00' AS TIME) AS StartTime,
           'Confirmed' AS Status,
           NULL AS CancellationReason

    UNION ALL
    SELECT 'mehmet@gmail.com', 'selin.doctor@mhrs.com',
           'Istanbul City Hospital', 'Neurology',
           1, '10:00', 'Completed', NULL

    UNION ALL
    SELECT 'zeynep@gmail.com', 'can.doctor@mhrs.com',
           'Ankara Central Hospital', 'Pediatrics',
           1, '09:00', 'Confirmed', NULL

    UNION ALL
    SELECT 'ali@gmail.com', 'ahmet.doctor@mhrs.com',
           'Izmir Ege Hospital', 'Cardiology',
           1, '10:00', 'Cancelled', 'Patient requested cancellation'

    UNION ALL
    SELECT 'elif@gmail.com', 'selin.doctor@mhrs.com',
           'Istanbul City Hospital', 'Dermatology',
           1, '11:00', 'Confirmed', NULL

    UNION ALL
    SELECT 'ayse@gmail.com', 'ahmet.doctor@mhrs.com',
           'Istanbul City Hospital', 'Cardiology',
           2, '09:00', 'Pending', NULL

    UNION ALL
    SELECT 'mehmet@gmail.com', 'can.doctor@mhrs.com',
           'Ankara Central Hospital', 'Pediatrics',
           2, '10:00', 'Confirmed', NULL

    UNION ALL
    SELECT 'zeynep@gmail.com', 'selin.doctor@mhrs.com',
           'Istanbul City Hospital', 'Neurology',
           2, '11:00', 'Confirmed', NULL
) A

INNER JOIN Users Citizen
    ON Citizen.Email = A.CitizenEmail

INNER JOIN AvailabilitySlots S
    ON S.SlotDate = DATEADD(DAY, A.DayOffset, CAST(GETDATE() AS DATE))
    AND S.StartTime = A.StartTime

INNER JOIN WorkSchedules W
    ON W.ScheduleID = S.ScheduleID

INNER JOIN DoctorAssignments DA
    ON DA.AssignmentID = W.AssignmentID

INNER JOIN Doctors D
    ON D.UserID = DA.DoctorID

INNER JOIN Users DoctorUser
    ON DoctorUser.UserID = D.UserID
    AND DoctorUser.Email = A.DoctorEmail

INNER JOIN Clinics C
    ON C.ClinicID = DA.ClinicID
    AND C.ClinicName = A.ClinicName

INNER JOIN Hospitals H
    ON H.HospitalID = C.HospitalID
    AND H.HospitalName = A.HospitalName;

    INSERT INTO WaitingListRequests
(CreatedAt, PreferredStartDate, PreferredEndDate, Status,
 CitizenUserID, ClinicID, DoctorID)

SELECT
    GETDATE(),
    DATEADD(DAY, 4, CAST(GETDATE() AS DATE)),
    DATEADD(DAY, 15, CAST(GETDATE() AS DATE)),
    R.Status,
    U.UserID,
    C.ClinicID,
    D.UserID

FROM (
    SELECT 'ayse@gmail.com' AS Email,
           'Cardiology' AS ClinicName,
           'Istanbul City Hospital' AS HospitalName,
           'ahmet.doctor@mhrs.com' AS DoctorEmail,
           'Waiting' AS Status

    UNION ALL
    SELECT 'mehmet@gmail.com',
           'Neurology',
           'Istanbul City Hospital',
           'selin.doctor@mhrs.com',
           'Waiting'

    UNION ALL
    SELECT 'zeynep@gmail.com',
           'Pediatrics',
           'Ankara Central Hospital',
           NULL,
           'Notified'

    UNION ALL
    SELECT 'elif@gmail.com',
           'Dermatology',
           'Istanbul City Hospital',
           NULL,
           'Cancelled'
) R

INNER JOIN Users U ON U.Email = R.Email
INNER JOIN Clinics C
    ON C.ClinicName = R.ClinicName
INNER JOIN Hospitals H
    ON H.HospitalID = C.HospitalID
    AND H.HospitalName = R.HospitalName
LEFT JOIN Users DU
    ON DU.Email = R.DoctorEmail
LEFT JOIN Doctors D
    ON D.UserID = DU.UserID;

    INSERT INTO Notifications
(Message, NotificationDate, NotificationType, IsRead,
 UserID, AppointmentID, RequestID)

SELECT
    N.Message,
    GETDATE(),
    N.NotificationType,
    N.IsRead,
    U.UserID,
    A.AppointmentID,
    R.RequestID

FROM (
    SELECT 'Your appointment has been confirmed.' AS Message,
           'Appointment' AS NotificationType,
           0 AS IsRead,
           'ayse@gmail.com' AS Email,
           'Confirmed' AS AppointmentStatus,
           'Cardiology' AS ClinicName,
           CAST(NULL AS NVARCHAR(30)) AS RequestStatus

    UNION ALL
    SELECT 'Your appointment has been completed.',
           'Appointment', 1,
           'mehmet@gmail.com', 'Completed',
           'Neurology', NULL

    UNION ALL
    SELECT 'Your appointment has been cancelled.',
           'Appointment', 0,
           'ali@gmail.com', 'Cancelled',
           'Cardiology', NULL

    UNION ALL
    SELECT 'Your appointment is waiting for confirmation.',
           'Appointment', 0,
           'ayse@gmail.com', 'Pending',
           'Cardiology', NULL

    UNION ALL
    SELECT 'Your appointment is confirmed.',
           'Appointment', 1,
           'zeynep@gmail.com', 'Confirmed',
           'Pediatrics', NULL

    UNION ALL
    SELECT 'You have been added to the waiting list.',
           'WaitingList', 0,
           'ayse@gmail.com', NULL,
           'Cardiology', 'Waiting'

    UNION ALL
    SELECT 'A suitable appointment opportunity is available.',
           'WaitingList', 0,
           'zeynep@gmail.com', NULL,
           'Pediatrics', 'Notified'

    UNION ALL
    SELECT 'Your waiting list request has been cancelled.',
           'WaitingList', 1,
           'elif@gmail.com', NULL,
           'Dermatology', 'Cancelled'

    UNION ALL
    SELECT 'Your appointment has been confirmed.',
           'Appointment', 0,
           'elif@gmail.com', 'Confirmed',
           'Dermatology', NULL

    UNION ALL
    SELECT 'Your waiting list request is being processed.',
           'WaitingList', 0,
           'mehmet@gmail.com', NULL,
           'Neurology', 'Waiting'
) N

INNER JOIN Users U ON U.Email = N.Email

LEFT JOIN Appointments A
    ON A.CitizenUserID = U.UserID
    AND A.Status = N.AppointmentStatus
    AND N.ClinicName IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM AvailabilitySlots S
        INNER JOIN WorkSchedules W ON W.ScheduleID = S.ScheduleID
        INNER JOIN DoctorAssignments DA ON DA.AssignmentID = W.AssignmentID
        INNER JOIN Clinics C ON C.ClinicID = DA.ClinicID
        WHERE S.SlotID = A.SlotID
        AND C.ClinicName = N.ClinicName
    )

LEFT JOIN WaitingListRequests R
    ON R.CitizenUserID = U.UserID
    AND R.Status = N.RequestStatus
    AND R.RequestID = (
        SELECT TOP 1 R2.RequestID
        FROM WaitingListRequests R2
        INNER JOIN Clinics C2 ON C2.ClinicID = R2.ClinicID
        WHERE R2.CitizenUserID = U.UserID
          AND R2.Status = N.RequestStatus
          AND C2.ClinicName = N.ClinicName
        ORDER BY R2.RequestID
    );

    INSERT INTO WorkSchedules
([Day], StartTime, EndTime, BreakStartTime,
 BreakEndTime, IsClosed, AssignmentID)

SELECT
    WorkDay,
    '09:00',
    '17:00',
    '12:00',
    '13:00',
    0,
    AssignmentID
FROM DoctorAssignments;

INSERT INTO AuditLogs
(ActionType, ActionDate, Description, UserID)

SELECT
    L.ActionType,
    DATEADD(MINUTE, -L.MinuteOffset, GETDATE()),
    L.Description,
    U.UserID

FROM (
    SELECT 'LOGIN' AS ActionType,
           60 AS MinuteOffset,
           'User logged into the system.' AS Description,
           'ayse@gmail.com' AS Email

    UNION ALL
    SELECT 'CREATE_APPOINTMENT', 55,
           'New appointment created.',
           'ayse@gmail.com'

    UNION ALL
    SELECT 'CANCEL_APPOINTMENT', 50,
           'Appointment cancelled by citizen.',
           'ali@gmail.com'

    UNION ALL
    SELECT 'LOGIN', 45,
           'Doctor logged into the system.',
           'ahmet.doctor@mhrs.com'

    UNION ALL
    SELECT 'UPDATE_SCHEDULE', 40,
           'Doctor schedule updated.',
           'ahmet.doctor@mhrs.com'

    UNION ALL
    SELECT 'LOGIN', 35,
           'Hospital manager logged in.',
           'manager@mhrs.com'

    UNION ALL
    SELECT 'ADD_HOSPITAL', 30,
           'Hospital information added.',
           'manager@mhrs.com'

    UNION ALL
    SELECT 'LOGIN', 25,
           'System administrator logged in.',
           'admin@mhrs.com'

    UNION ALL
    SELECT 'UPDATE_USER', 20,
           'User information updated.',
           'admin@mhrs.com'

    UNION ALL
    SELECT 'CREATE_WAITING_LIST', 15,
           'Waiting list request created.',
           'zeynep@gmail.com'
) L
INNER JOIN Users U ON U.Email = L.Email;



SELECT 'Users' AS TableName, COUNT(*) AS Total FROM Users
UNION ALL
SELECT 'Citizens', COUNT(*) FROM Citizens
UNION ALL
SELECT 'Doctors', COUNT(*) FROM Doctors
UNION ALL
SELECT 'HospitalManagers', COUNT(*) FROM HospitalManagers
UNION ALL
SELECT 'SystemManagers', COUNT(*) FROM SystemManagers
UNION ALL
SELECT 'Provinces', COUNT(*) FROM Provinces
UNION ALL
SELECT 'Districts', COUNT(*) FROM Districts
UNION ALL
SELECT 'Hospitals', COUNT(*) FROM Hospitals
UNION ALL
SELECT 'Clinics', COUNT(*) FROM Clinics
UNION ALL
SELECT 'DoctorAssignments', COUNT(*) FROM DoctorAssignments
UNION ALL
SELECT 'WorkSchedules', COUNT(*) FROM WorkSchedules
UNION ALL
SELECT 'AvailabilitySlots', COUNT(*) FROM AvailabilitySlots
UNION ALL
SELECT 'Appointments', COUNT(*) FROM Appointments
UNION ALL
SELECT 'Notifications', COUNT(*) FROM Notifications
UNION ALL
SELECT 'WaitingListRequests', COUNT(*) FROM WaitingListRequests
UNION ALL
SELECT 'AuditLogs', COUNT(*) FROM AuditLogs;


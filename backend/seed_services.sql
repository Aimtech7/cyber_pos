-- Ensure category column exists (idempotent)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'services' AND column_name = 'category') THEN 
        ALTER TABLE services ADD COLUMN category VARCHAR(50); 
    END IF; 
END $$;

-- Insert or Update Services
INSERT INTO services (name, category, pricing_mode, base_price, description, is_active, requires_stock)
VALUES 
    -- A) Core Services
    ('Internet Browsing (Per Minute)', 'Core', 'PER_MINUTE', 2.00, 'Standard internet access charged per minute', TRUE, FALSE),
    ('Printing (Black & White)', 'Core', 'PER_PAGE', 10.00, 'A4 Black and White printing', TRUE, TRUE),
    ('Printing (Color)', 'Core', 'PER_PAGE', 20.00, 'A4 Color printing', TRUE, TRUE),
    ('Scanning', 'Core', 'PER_PAGE', 30.00, 'Document scanning per page', TRUE, FALSE),
    ('Photocopy (Black & White)', 'Core', 'PER_PAGE', 5.00, 'A4 Black and White photocopy', TRUE, TRUE),
    ('Photocopy (Color)', 'Core', 'PER_PAGE', 10.00, 'A4 Color photocopy', TRUE, TRUE),
    ('Binding (Spiral)', 'Core', 'PER_JOB', 70.00, 'Spiral document binding', TRUE, TRUE),
    ('Lamination (A4)', 'Core', 'PER_JOB', 50.00, 'A4 Document lamination', TRUE, TRUE),
    ('Typesetting', 'Core', 'PER_JOB', 50.00, 'Document typing service (base price)', TRUE, FALSE),

    -- B) Government & Legal
    ('eCitizen Services Assistance', 'Government', 'PER_JOB', 200.00, 'Assistance with eCitizen portal services', TRUE, FALSE),
    ('KRA PIN Registration', 'Government', 'PER_JOB', 300.00, 'New KRA PIN registration', TRUE, FALSE),
    ('KRA Returns Filing', 'Government', 'PER_JOB', 500.00, 'Filing of KRA tax returns', TRUE, FALSE),
    ('NTSA TIMS Services', 'Government', 'PER_JOB', 300.00, 'NTSA portal assistance', TRUE, FALSE),
    ('HELB Application', 'Government', 'PER_JOB', 400.00, 'Higher Education Loans Board application', TRUE, FALSE),
    ('Good Conduct Application', 'Government', 'PER_JOB', 300.00, 'Police Clearance Certificate application', TRUE, FALSE),
    ('SHA/NHIF Registration', 'Government', 'PER_JOB', 250.00, 'Social Health Authority / NHIF registration', TRUE, FALSE),
    ('NSSF Registration', 'Government', 'PER_JOB', 200.00, 'National Social Security Fund registration', TRUE, FALSE),

    -- C) Job & School
    ('CV Writing (Professional)', 'Job & School', 'PER_JOB', 800.00, 'Professional Curriculum Vitae creation', TRUE, FALSE),
    ('Cover Letter Writing', 'Job & School', 'PER_JOB', 400.00, 'Professional cover letter writing', TRUE, FALSE),
    ('Job Application Submission', 'Job & School', 'PER_JOB', 200.00, 'Assistance with online job applications', TRUE, FALSE),
    ('KUCCPS Application', 'Job & School', 'PER_JOB', 300.00, 'University placement application', TRUE, FALSE),
    ('University Application', 'Job & School', 'PER_JOB', 500.00, 'Direct university application assistance', TRUE, FALSE),
    ('Document Editing & Formatting', 'Job & School', 'PER_JOB', 150.00, 'Professional document formatting', TRUE, FALSE),

    -- D) Advanced Print
    ('Passport Photo Printing', 'Printing', 'PER_JOB', 150.00, 'Printing of passport size photos', TRUE, TRUE),
    ('Bulk Printing (Discounted)', 'Printing', 'PER_PAGE', 8.00, 'Discounted rate for bulk printing', TRUE, TRUE),
    ('Exam / Past Paper Printing', 'Printing', 'PER_JOB', 100.00, 'Printing of exam papers', TRUE, TRUE),
    ('Poster Printing (A3)', 'Printing', 'PER_JOB', 200.00, 'A3 size poster printing', TRUE, TRUE),
    ('Certificate Printing (Color)', 'Printing', 'PER_JOB', 300.00, 'High quality certificate printing', TRUE, TRUE),

    -- E) Digital Services
    ('Email Creation', 'Digital', 'PER_JOB', 150.00, 'Creation of new email account', TRUE, FALSE),
    ('Online Account Recovery', 'Digital', 'PER_JOB', 300.00, 'Assistance with recovering online accounts', TRUE, FALSE),
    ('Online Shopping Assistance', 'Digital', 'PER_JOB', 300.00, 'Assistance with online purchases', TRUE, FALSE),
    ('Digital Business Card Setup', 'Digital', 'PER_JOB', 1000.00, 'Setup of digital business card', TRUE, FALSE),
    ('Social Media Setup', 'Digital', 'PER_JOB', 500.00, 'Setup of social media profiles', TRUE, FALSE),

    -- F) Business & Professional
    ('Company Registration Assistance', 'Business', 'PER_JOB', 2500.00, 'Assistance with business registration', TRUE, FALSE),
    ('Business Name Search', 'Business', 'PER_JOB', 500.00, 'Search for business name availability', TRUE, FALSE),
    ('Tender Document Preparation', 'Business', 'PER_JOB', 1500.00, 'Assistance preparing tender documents', TRUE, FALSE),
    ('Proposal Writing Assistance', 'Business', 'PER_JOB', 2000.00, 'Help with writing business proposals', TRUE, FALSE),
    ('Logo Design (Basic)', 'Business', 'PER_JOB', 1500.00, 'Basic logo design service', TRUE, FALSE),

    -- G) Premium Cyber
    ('PC Usage (Gaming Hour)', 'Premium', 'PER_JOB', 100.00, 'High-performance PC usage per hour', TRUE, FALSE),
    ('Software Installation', 'Premium', 'PER_JOB', 500.00, 'Installation of standard software', TRUE, FALSE),
    ('Phone Flashing / Software Update', 'Premium', 'PER_JOB', 800.00, 'Mobile phone software services', TRUE, FALSE),
    ('WiFi Setup Assistance', 'Premium', 'PER_JOB', 1000.00, 'Configuration of WiFi devices', TRUE, FALSE),
    ('Basic Cybersecurity Check', 'Premium', 'PER_JOB', 1500.00, 'Basic security audit for personal devices', TRUE, FALSE),

    -- H) Packages
    ('Job Application Package', 'Packages', 'PER_JOB', 1200.00, 'CV, Cover Letter, and Application submission', TRUE, FALSE),
    ('University Application Package', 'Packages', 'PER_JOB', 1000.00, 'KUCCPS + University application + printing', TRUE, FALSE),
    ('Government Service Package', 'Packages', 'PER_JOB', 600.00, 'eCitizen + KRA + NSSF registration bundle', TRUE, FALSE)

ON CONFLICT (name) DO UPDATE SET
    category = EXCLUDED.category,
    pricing_mode = EXCLUDED.pricing_mode,
    base_price = EXCLUDED.base_price,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    requires_stock = EXCLUDED.requires_stock;

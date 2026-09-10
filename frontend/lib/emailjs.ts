import emailjs from "@emailjs/browser";

interface SendAuthEmailParams {
  toEmail: string;
  toName: string;
  actionType: "login" | "signup" | "reset_password";
}

export interface EmailJSResult {
  success: boolean;
  error?: string;
}

/**
 * Helper to send notification emails via EmailJS
 */
export async function sendAuthEmail({ toEmail, toName, actionType }: SendAuthEmailParams): Promise<EmailJSResult> {
  const serviceId = process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID || "service_courfb4";
  const templateId = process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID || "template_4mydnpd";
  const publicKey = process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY || "QvOsCURi0Qe0daPGD";

  const name = toName || toEmail.split("@")[0];

  const templateParams = {
    to_email: toEmail,
    email: toEmail,
    user_email: toEmail,
    reply_to: toEmail,
    to_name: name,
    user_name: name,
    action_type: actionType,
    message: actionType === "signup"
      ? "Welcome to PatentLens AI! Your account has been created successfully."
      : actionType === "login"
      ? "New login detected on your PatentLens AI account."
      : "A password reset request was initiated for your PatentLens AI account.",
    time_stamp: new Date().toLocaleString()
  };

  try {
    const response = await emailjs.send(serviceId, templateId, templateParams, publicKey);
    console.log(`[EmailJS] ${actionType} notification successfully sent to ${toEmail}:`, response);
    return { success: true };
  } catch (error: any) {
    const errText = error?.text || error?.message || JSON.stringify(error);
    console.warn(`[EmailJS Error] Could not send ${actionType} email to ${toEmail}:`, errText);
    return { success: false, error: errText };
  }
}

/**
 * Helper to send 6-digit OTP verification email via EmailJS
 */
export async function sendOTPEmail({ toEmail, toName, otpCode }: { toEmail: string; toName?: string; otpCode: string }): Promise<EmailJSResult> {
  const serviceId = process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID || "service_courfb4";
  const templateId = process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID || "template_4mydnpd";
  const publicKey = process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY || "QvOsCURi0Qe0daPGD";

  const name = toName || toEmail.split("@")[0];
  // Ensure a valid 6-digit random OTP is always generated
  const activeOtp = (otpCode && String(otpCode).trim().length === 6)
    ? String(otpCode).trim()
    : Math.floor(100000 + Math.random() * 900000).toString();

  const templateParams = {
    // Recipient & User Name keys
    to_email: toEmail,
    email: toEmail,
    user_email: toEmail,
    reply_to: toEmail,
    to_name: name,
    name: name,
    user_name: name,
    username: name,
    recipient_name: name,
    first_name: name,
    user: name,

    // Action & Message keys
    action_type: "otp_verification",
    message: `Your PatentLens AI First-Time Verification OTP is: ${activeOtp}. Valid for 10 minutes.`,
    time_stamp: new Date().toLocaleString(),

    // OTP Code Keys (All common EmailJS template placeholder names)
    otp_code: activeOtp,
    otp: activeOtp,
    OTP: activeOtp,
    OTP_CODE: activeOtp,
    Otp: activeOtp,
    code: activeOtp,
    CODE: activeOtp,
    passcode: activeOtp,
    PASSCODE: activeOtp,
    Passcode: activeOtp,
    pass_code: activeOtp,
    verification_code: activeOtp,
    verificationCode: activeOtp,
    one_time_password: activeOtp,
    oneTimePassword: activeOtp,
    token: activeOtp,
    TOKEN: activeOtp,
    Token: activeOtp,
    auth_code: activeOtp,
    verify_code: activeOtp,
    user_otp: activeOtp,
    security_code: activeOtp,
    verification_number: activeOtp,
    key: activeOtp,
    KEY: activeOtp,
    password: activeOtp,
    PASSWORD: activeOtp,
    pin: activeOtp,
    PIN: activeOtp,
    secret_code: activeOtp,
    number: activeOtp,
    value: activeOtp,

    // Time Expiry & Validity Keys (For "valid for {{minutes}} minutes")
    minutes: "10",
    valid_minutes: "10",
    expiry_minutes: "10",
    expiry: "10",
    validity: "10",
    time_expiry: "10",
    time: "10 minutes",
    valid_time: "10",
    time_limit: "10",
    expire_time: "10",
    expiration_time: "10",
    valid_for: "10",
    duration: "10",
    period: "10",
    validity_period: "10",
    min: "10",
    MIN: "10"
  };

  try {
    const response = await emailjs.send(serviceId, templateId, templateParams, publicKey);
    console.log(`[EmailJS OTP] Verification email with code ${activeOtp} successfully sent to ${toEmail}:`, response);
    return { success: true };
  } catch (error: any) {
    const errText = error?.text || error?.message || JSON.stringify(error);
    console.warn(`[EmailJS OTP Error] Verification email dispatch issue for ${toEmail}:`, errText);
    return { success: false, error: errText };
  }
}

import emailjs from "@emailjs/browser";

interface SendAuthEmailParams {
  toEmail: string;
  toName: string;
  actionType: "login" | "signup" | "reset_password";
}

/**
 * Helper to send notification emails via EmailJS
 */
export async function sendAuthEmail({ toEmail, toName, actionType }: SendAuthEmailParams): Promise<boolean> {
  const serviceId = process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID || "service_patentlens";
  const templateId = process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID || "template_auth_alert";
  const publicKey = process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY || "user_demo_public_key";

  const templateParams = {
    to_email: toEmail,
    to_name: toName || toEmail.split("@")[0],
    action_type: actionType,
    message: actionType === "signup"
      ? "Welcome to PatentLens AI! Your account has been created successfully."
      : actionType === "login"
      ? "New login detected on your PatentLens AI account."
      : "A password reset request was initiated for your PatentLens AI account.",
    time_stamp: new Date().toLocaleString()
  };

  try {
    // Attempt sending email via EmailJS
    await emailjs.send(serviceId, templateId, templateParams, publicKey);
    console.log(`[EmailJS] ${actionType} notification sent to ${toEmail}`);
    return true;
  } catch (error) {
    // Graceful fallback logging if EmailJS credentials are not configured yet
    console.warn(`[EmailJS] Could not send email via API (check process.env.NEXT_PUBLIC_EMAILJS_*):`, error);
    return false;
  }
}

import { Amplify } from "aws-amplify";

// AWS Amplify設定
const amplifyConfig = {
  Auth: {
    Cognito: {
      // ユーザープール設定
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || "",
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || "",

      // 認証フロー設定
      loginWith: {
        email: true,
        username: false,
      },

      // アカウント設定
      signUpVerificationMethod: "code" as const, // メール認証
      userAttributes: {
        email: {
          required: true,
        },
      },
    },
  },
};

// Amplifyを設定
export const configureAmplify = () => {
  try {
    Amplify.configure(amplifyConfig);
    console.log("AWS Amplify設定が完了しました");
  } catch (error) {
    console.error("AWS Amplify設定エラー:", error);
  }
};

export default amplifyConfig;

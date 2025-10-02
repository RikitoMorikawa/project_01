/**
 * 簡単なテスト動作確認
 * Simple test verification
 */

/// <reference types="jest" />

describe("基本テスト / Basic Tests", () => {
  it("Jestが正常に動作する / Jest works correctly", () => {
    expect(1 + 1).toBe(2);
  });

  it("文字列のテスト / String test", () => {
    expect("hello").toBe("hello");
  });

  it("配列のテスト / Array test", () => {
    const arr = [1, 2, 3];
    expect(arr).toHaveLength(3);
    expect(arr).toContain(2);
  });

  it("オブジェクトのテスト / Object test", () => {
    const obj = { name: "test", value: 42 };
    expect(obj).toHaveProperty("name");
    expect(obj.name).toBe("test");
  });

  it("非同期テスト / Async test", async () => {
    const promise = Promise.resolve("success");
    await expect(promise).resolves.toBe("success");
  });
});

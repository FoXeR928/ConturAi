package main

import (
	"bufio"
	"crypto/rand"
	"fmt"
	"io"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

func runCmd(dir string, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}

func dc(projectDir string, args ...string) bool {
	composeFile := filepath.Join(projectDir, "docker-compose.yml")
	fullArgs := append([]string{"compose", "-f", composeFile}, args...)
	err := runCmd(projectDir, "docker", fullArgs...)
	if err != nil {
		fmt.Printf("\n[ERROR] Ошибка Docker Compose: %v\n", err)
		return false
	}
	return true
}

func generatePassword(length int) string {
	const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	result := make([]byte, length)
	for i := range result {
		num, _ := rand.Int(rand.Reader, big.NewInt(int64(len(chars))))
		result[i] = chars[num.Int64()]
	}
	return string(result)
}

func findProjectRoot() string {
	exePath, err := os.Executable()
	if err != nil {
		dir, _ := os.Getwd()
		return dir
	}
	dir := filepath.Dir(exePath)

	// Проверяем, есть ли docker-compose.yml или папка templates
	if _, err := os.Stat(filepath.Join(dir, "templates")); err == nil {
		return dir
	}

	parentDir := filepath.Dir(dir)
	if _, err := os.Stat(filepath.Join(parentDir, "templates")); err == nil {
		return parentDir
	}

	return dir
}

// КОПИРОВАНИЕ ШАБЛОНА DOCKER-COMPOSE
func setupCompose(projectDir string) {
	composePath := filepath.Join(projectDir, "docker-compose.yml")
	templatePath := filepath.Join(projectDir, "templates", "docker-compose.yml")

	// Если конфиг уже есть, не перезаписываем (чтобы не сломать настройки)
	if _, err := os.Stat(composePath); err == nil {
		fmt.Println("[INFO] Файл docker-compose.yml уже существует.")
		return
	}

	fmt.Println("[INFO] Создание docker-compose.yml из шаблона...")
	
	srcFile, err := os.Open(templatePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не найден шаблон: %s\n", templatePath)
		os.Exit(1)
	}
	defer srcFile.Close()

	dstFile, err := os.Create(composePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не удалось создать %s\n", composePath)
		os.Exit(1)
	}
	defer dstFile.Close()

	_, err = io.Copy(dstFile, srcFile)
	if err != nil {
		fmt.Println("[ERROR] Ошибка при копировании файла.")
		os.Exit(1)
	}
	fmt.Println("[OK] docker-compose.yml создан.")
}

func ensureLockFile(projectDir string) {
	// ... (код из предыдущего сообщения)
}

func setupEnv(projectDir string) {
	// ... (код из предыдущего сообщения, который берет шаблон из templates/.env.example)
}

func main() {
	fmt.Println("==================================================")
	fmt.Println("  ConturAI Core - Установщик (v3.0)")
	fmt.Println("==================================================")

	if err := runCmd(".", "docker", "info"); err != nil {
		fmt.Println("\n[ERROR] Docker не запущен.")
		os.Exit(1)
	}

	projectDir := findProjectRoot()
	fmt.Printf("[INFO] Рабочая директория: %s\n", projectDir)

	ensureLockFile(projectDir)
	setupEnv(projectDir)
	
	// ВЫЗЫВАЕМ НОВУЮ ФУНКЦИЮ
	setupCompose(projectDir)

	fmt.Println("\n[INFO] Сборка и запуск Бэкенда и Базы Данных...")
	dc(projectDir, "down", "--remove-orphans")
	if !dc(projectDir, "up", "-d", "--build") {
		os.Exit(1)
	}

	fmt.Println("\n[INFO] Ожидание запуска базы данных (10 секунд)...")
	time.Sleep(10 * time.Second)

	fmt.Println("\n[INFO] Создание таблиц и администратора...")
	runCmd(projectDir, "docker", "compose", "exec", "-T", "backend", "python", "scripts/manage.py", "init-db")
	runCmd(projectDir, "docker", "compose", "exec", "-T", "backend", "python", "scripts/manage.py", "reset-admin")

	fmt.Println("\n==================================================")
	fmt.Println("  УСТАНОВКА ЗАВЕРШЕНА!")
	fmt.Println("  API и Swagger доступны: http://localhost:8000/docs")
	fmt.Println("==================================================")
	
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Нажмите Enter для выхода...")
	reader.ReadString('\n')
}
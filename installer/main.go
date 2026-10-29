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

	// 1. Если exe лежит в корне (там есть папка templates)
	if _, err := os.Stat(filepath.Join(dir, "templates")); err == nil {
		return dir
	}

	// 2. Если exe лежит в папке bin (поднимаемся на уровень выше)
	parentDir := filepath.Dir(dir)
	if _, err := os.Stat(filepath.Join(parentDir, "templates")); err == nil {
		return parentDir
	}

	// 3. Если запустили из терминала (go run) или exe в неизвестном месте
	currentDir, _ := os.Getwd()
	if _, err := os.Stat(filepath.Join(currentDir, "templates")); err == nil {
		return currentDir
	}

	return dir
}

// Генерация uv.lock, если его нет
func ensureLockFile(projectDir string) {
	backendDir := filepath.Join(projectDir, "backend_core")
	lockFile := filepath.Join(backendDir, "uv.lock")
	pyprojectFile := filepath.Join(backendDir, "pyproject.toml")

	// Если лок-файл есть, ничего не делаем
	if _, err := os.Stat(lockFile); err == nil {
		return
	}

	// Проверяем, существует ли pyproject.toml
	if _, err := os.Stat(pyprojectFile); os.IsNotExist(err) {
		fmt.Println("\n[ERROR] Не найден файл pyproject.toml!")
		fmt.Printf("Установщик искал его по пути: %s\n", pyprojectFile)
		fmt.Println("Проверьте, что папка 'backend_core' находится в корне проекта и содержит файл 'pyproject.toml'.")
		fmt.Println("Также убедитесь, что вы запускаете установщик из папки 'bin/' или из корня проекта.")
		os.Exit(1)
	}

	fmt.Println("\n[WARN] Файл uv.lock не найден. Генерируем автоматически...")
	fmt.Println("[INFO] Это может занять около минуты...")

	err := runCmd(projectDir, "docker", "run", "--rm",
		"-v", fmt.Sprintf("%s:/app", backendDir),
		"-w", "/app",
		"-e", "UV_PROJECT_ENVIRONMENT=/tmp/uv-venv",
		"python:3.12-slim",
		"sh", "-c", "pip install --quiet uv==0.5.11 && uv lock")

	if err != nil {
		fmt.Println("\n[ERROR] Не удалось сгенерировать uv.lock.")
		fmt.Println("Убедитесь, что Docker имеет доступ к интернету.")
		os.Exit(1)
	}
	fmt.Println("[OK] uv.lock успешно создан.")
}

// Копирование шаблона docker-compose
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

// Создание .env из шаблона
func setupEnv(projectDir string) {
	envPath := filepath.Join(projectDir, ".env")
	examplePath := filepath.Join(projectDir, "templates", ".env.example")

	if _, err := os.Stat(envPath); err == nil {
		fmt.Println("[INFO] Файл .env уже существует. Используем текущие настройки.")
		return
	}

	fmt.Println("[INFO] Создание нового .env с безопасным паролем...")
	password := generatePassword(24)
	
	content, err := os.ReadFile(examplePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не найден шаблон: %s\n", examplePath)
		fmt.Println("Убедитесь, что папка templates содержит файл .env.example.")
		os.Exit(1)
	}

	newContent := strings.Replace(string(content), "DB_PASSWORD=CHANGE_ME", "DB_PASSWORD="+password, 1)
	os.WriteFile(envPath, []byte(newContent), 0644)
	fmt.Println("[OK] Файл .env создан в корне проекта.")
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
	setupCompose(projectDir)

	// 1. Собираем образы
	fmt.Println("\n[INFO] Сборка Docker-образов (это может занять время)...")
	if !dc(projectDir, "build") {
		os.Exit(1)
	}

	// 2. Запускаем ТОЛЬКО базу данных
	fmt.Println("\n[INFO] Запуск Базы Данных...")
	dc(projectDir, "up", "-d", "postgres")

	fmt.Println("[INFO] Ожидание запуска базы данных (10 секунд)...")
	time.Sleep(10 * time.Second)

	// 3. Инициализируем БД через одноразовый контейнер (он не запустит FastAPI)
	fmt.Println("\n[INFO] Создание таблиц и администратора...")
	runCmd(projectDir, "docker", "compose", "run", "--rm", "backend", "python", "scripts/manage.py", "init-db")
	runCmd(projectDir, "docker", "compose", "run", "--rm", "backend", "python", "scripts/manage.py", "reset-admin")

	// 4. Запускаем сам бэкенд
	fmt.Println("\n[INFO] Запуск Бэкенда...")
	if !dc(projectDir, "up", "-d") {
		os.Exit(1)
	}

	fmt.Println("\n==================================================")
	fmt.Println("  УСТАНОВКА ЗАВЕРШЕНА!")
	fmt.Println("  API и Swagger доступны: http://localhost:8000/docs")
	fmt.Println("==================================================")
	
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Нажмите Enter для выхода...")
	reader.ReadString('\n')
}
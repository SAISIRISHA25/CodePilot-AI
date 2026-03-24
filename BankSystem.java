import java.util.ArrayList;
import java.util.Scanner;
public class BankSystem {
    static ArrayList<Customer> customers = new ArrayList<>();
    static Scanner sc = new Scanner(System.in);
    static final double MIN_BALANCE = 1000.0;

    public static void main(String[] args) {
        int choice;

        do {
            System.out.println("\n===== BANK MANAGEMENT SYSTEM =====");
            System.out.println("1. Create Account");
            System.out.println("2. Deposit Amount");
            System.out.println("3. Withdraw Amount");
            System.out.println("4. Balance Enquiry");
            System.out.println("5. Transfer Amount");
            System.out.println("6. Search Customer by Account Number");
            System.out.println("7. Display All Customers");
            System.out.println("8. Exit");
            System.out.print("Enter your choice: ");
            choice = sc.nextInt();

            switch (choice) {
                case 1:
                    createAccount();
                    break;
                case 2:
                    depositAmount();
                    break;
                case 3:
                    withdrawAmount();
                    break;
                case 4:
                    enquiryBalance();
                    break;
                case 5:
                    transferAmount();
                    break;
                case 6:
                    searchCustomer();
                    break;
                case 7:
                    displayAllCustomers();
                    break;
                case 8:
                    System.out.println("Exiting program...");
                    break;
                default:
                    System.out.println("Invalid choice!");
            }
        } while (choice != 8);
    }

    static void createAccount() {
        System.out.print("Enter Account Number: ");
        int accNo = sc.nextInt();
        sc.nextLine();

        if (findCustomer(accNo) != null) {
            System.out.println("Account number already exists!");
            return;
        }

        System.out.print("Enter Name: ");
        String name = sc.nextLine();

        System.out.print("Enter Initial Balance: ");
        double balance = sc.nextDouble();
        sc.nextLine();

        if (balance < MIN_BALANCE) {
            System.out.println("Initial balance must be at least " + MIN_BALANCE);
            return;
        }

        System.out.print("Enter Account Type: ");
        String accountType = sc.nextLine();

        System.out.print("Enter Email: ");
        String email = sc.nextLine();

        if (!isValidEmail(email)) {
            System.out.println("Invalid email format!");
            return;
        }

        Customer customer = new Customer(accNo, name, balance, accountType, email);
        customers.add(customer);
        System.out.println("Account created successfully.");
    }

    static void depositAmount() {
        System.out.print("Enter Account Number: ");
        int accNo = sc.nextInt();

        Customer customer = findCustomer(accNo);

        if (customer == null) {
            System.out.println("Account not found!");
            return;
        }

        System.out.print("Enter Deposit Amount: ");
        double amount = sc.nextDouble();

        if (amount <= 0) {
            System.out.println("Deposit amount must be greater than 0.");
            return;
        }

        customer.setBalance(customer.getBalance() + amount);
        System.out.println("Deposit successful.");
        System.out.println("Updated Balance: " + customer.getBalance());
    }

    static void withdrawAmount() {
        System.out.print("Enter Account Number: ");
        int accNo = sc.nextInt();

        Customer customer = findCustomer(accNo);

        if (customer == null) {
            System.out.println("Account not found!");
            return;
        }

        System.out.print("Enter Withdraw Amount: ");
        double amount = sc.nextDouble();

        if (amount <= 0) {
            System.out.println("Withdraw amount must be greater than 0.");
            return;
        }

        if (customer.getBalance() - amount < MIN_BALANCE) {
            System.out.println("Insufficient balance! Minimum balance of " + MIN_BALANCE + " must be maintained.");
            return;
        }

        customer.setBalance(customer.getBalance() - amount);
        System.out.println("Withdrawal successful.");
        System.out.println("Updated Balance: " + customer.getBalance());
    }

    static void enquiryBalance() {
        System.out.print("Enter Account Number: ");
        int accNo = sc.nextInt();

        Customer customer = findCustomer(accNo);

        if (customer == null) {
            System.out.println("Account not found!");
            return;
        }

        System.out.println("Account Holder : " + customer.getName());
        System.out.println("Current Balance: " + customer.getBalance());
    }

    static void transferAmount() {
        System.out.print("Enter From Account Number: ");
        int fromAcc = sc.nextInt();

        System.out.print("Enter To Account Number: ");
        int toAcc = sc.nextInt();

        if (fromAcc == toAcc) {
            System.out.println("Self transfer is not allowed!");
            return;
        }

        Customer sender = findCustomer(fromAcc);
        Customer receiver = findCustomer(toAcc);

        if (sender == null) {
            System.out.println("Sender account not found!");
            return;
        }

        if (receiver == null) {
            System.out.println("Receiver account not found!");
            return;
        }

        System.out.print("Enter Transfer Amount: ");
        double amount = sc.nextDouble();

        if (amount <= 0) {
            System.out.println("Transfer amount must be greater than 0.");
            return;
        }

        if (sender.getBalance() - amount < MIN_BALANCE) {
            System.out.println("Transfer failed! Minimum balance of " + MIN_BALANCE + " must be maintained.");
            return;
        }

        sender.setBalance(sender.getBalance() - amount);
        receiver.setBalance(receiver.getBalance() + amount);

        System.out.println("Transfer successful.");
        System.out.println("Sender Updated Balance   : " + sender.getBalance());
        System.out.println("Receiver Updated Balance : " + receiver.getBalance());
    }

    static void searchCustomer() {
        System.out.print("Enter Account Number to Search: ");
        int accNo = sc.nextInt();

        Customer customer = findCustomer(accNo);

        if (customer == null) {
            System.out.println("Customer not found!");
        } else {
            customer.display();
        }
    }

    static void displayAllCustomers() {
        if (customers.isEmpty()) {
            System.out.println("No customers available.");
            return;
        }

        System.out.println("\n===== CUSTOMER DETAILS =====");
        for (Customer customer : customers) {
            customer.display();
        }
    }

    static Customer findCustomer(int accountNumber) {
        for (Customer customer : customers) {
            if (customer.getAccountNumber() == accountNumber) {
                return customer;
            }
        }
        return null;
    }

    static boolean isValidEmail(String email) {
        return email.contains("@") && email.contains(".") && email.indexOf('@') > 0;
    }
}